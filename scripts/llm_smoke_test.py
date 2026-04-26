"""Real-LLM end-to-end smoke test for py-iku's convert_with_llm path.

Closes the wave-1 verification gap: every LLM-path agent in the
ultrareview had to use ``MockProvider`` because no API key was set.
This script reads the key from ``.env.local`` (gitignored), exercises
the LLM path against several representative pandas snippets, and
validates that each produces a sensible DataikuFlow.

Usage:
    1. Edit .env.local — fill in ANTHROPIC_API_KEY=sk-ant-...
    2. Run: python scripts/llm_smoke_test.py
       (or: python scripts/llm_smoke_test.py --provider openai)

The key is loaded into the current process's environ ONLY for the
duration of the script; it never persists, never enters the git
history, and never appears in conversation transcripts.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> dict[str, str]:
    """Tiny KEY=value parser. No deps, no quoting, no shell interpolation."""
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        # Strip surrounding quotes if user added them despite the warning.
        if (v.startswith('"') and v.endswith('"')) or (
            v.startswith("'") and v.endswith("'")
        ):
            v = v[1:-1]
        if k:
            out[k] = v
    return out


def _resolve_provider_and_key(
    provider: str, env: dict[str, str]
) -> tuple[str, Optional[str]]:
    """Pick the right env var for the chosen provider; return (provider, key)."""
    var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    # Prefer the .env.local value, fall back to whatever is already exported.
    key = env.get(var) or os.environ.get(var)
    return var, key


# Representative pandas snippets exercising different DSS recipe types.
EXAMPLES: list[tuple[str, str, set[str]]] = [
    (
        "groupby_agg",
        """
import pandas as pd
df = pd.read_csv('sales.csv')
df = df.dropna()
result = df.groupby('category').agg({'amount': 'sum'})
""",
        {"prepare", "grouping"},
    ),
    (
        "join_inner",
        """
import pandas as pd
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
merged = pd.merge(customers, orders, on='customer_id', how='inner')
""",
        {"join"},
    ),
    (
        "drop_duplicates",
        """
import pandas as pd
df = pd.read_csv('events.csv')
unique_events = df.drop_duplicates(subset=['user_id', 'event_id'])
""",
        # Both DISTINCT and PREPARE are valid for this — accept either.
        {"distinct", "prepare"},
    ),
    (
        "topn",
        """
import pandas as pd
df = pd.read_csv('users.csv')
top10 = df.nlargest(10, 'spend')
""",
        {"topn"},
    ),
    (
        "rolling_window",
        """
import pandas as pd
df = pd.read_csv('metrics.csv')
df['rolling_avg'] = df['value'].rolling(7).mean()
""",
        {"window"},
    ),
    (
        "compound_filter",
        """
import pandas as pd
df = pd.read_csv('transactions.csv')
suspicious = df[(df['amount'] > 1000) & (df['country'] != 'US')]
""",
        # Either SPLIT recipe or PREPARE+FilterOnFormula is acceptable.
        {"split", "prepare"},
    ),
    (
        "full_etl",
        """
import pandas as pd
customers = pd.read_csv('customers.csv')
orders = pd.read_csv('orders.csv')
customers = customers.dropna(subset=['customer_id'])
customers['name'] = customers['name'].str.upper()
merged = pd.merge(customers, orders, on='customer_id', how='left')
summary = merged.groupby('region').agg({'amount': ['sum', 'mean']})
result = summary.sort_values('amount', ascending=False)
""",
        {"prepare", "join", "grouping", "sort"},
    ),
]


def _run_one(name: str, code: str, expected_types: set[str], provider: str) -> dict:
    """Run convert_with_llm on a snippet and validate the resulting flow."""
    from py2dataiku import convert_with_llm

    events: list[tuple[str, dict]] = []

    def cb(phase: str, info: dict) -> None:
        events.append((phase, info))

    t0 = time.perf_counter()
    try:
        flow = convert_with_llm(code, provider=provider, on_progress=cb)
    except Exception as e:
        return {
            "name": name,
            "ok": False,
            "error": f"{e.__class__.__name__}: {e}",
            "elapsed_s": time.perf_counter() - t0,
        }
    elapsed = time.perf_counter() - t0

    actual_types = {r.recipe_type.value for r in flow.recipes}
    missing = expected_types - actual_types
    has_python_only = actual_types == {"python"}
    return {
        "name": name,
        "ok": not has_python_only and not missing,
        "elapsed_s": elapsed,
        "recipes": len(flow.recipes),
        "datasets": len(flow.datasets),
        "actual_types": sorted(actual_types),
        "expected_subset": sorted(expected_types),
        "missing": sorted(missing),
        "phases": [p for p, _ in events],
        "model": (events[1][1].get("model") if len(events) > 1 else None),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider",
        choices=("anthropic", "openai"),
        default="anthropic",
        help="LLM provider (default: anthropic)",
    )
    parser.add_argument(
        "--env-file",
        default=str(REPO_ROOT / ".env.local"),
        help="Path to .env.local (default: <repo>/.env.local)",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Run only these examples by name (default: all)",
    )
    args = parser.parse_args()

    # Load .env.local INTO os.environ (process-local; never persisted).
    env_path = Path(args.env_file)
    file_env = _load_env_file(env_path)
    var, key = _resolve_provider_and_key(args.provider, file_env)

    if not key:
        print(
            f"ERROR: no {var} found.\n"
            f"  - Edit {env_path} and add: {var}=<your-key>\n"
            f"  - Or export {var} in your shell before running.\n",
            file=sys.stderr,
        )
        return 2

    # Inject into the running process's environ ONLY (does not persist).
    os.environ[var] = key

    # Make py2dataiku importable when the repo isn't installed.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    examples = EXAMPLES
    if args.only:
        chosen = set(args.only)
        examples = [e for e in examples if e[0] in chosen]
        if not examples:
            print(f"No examples match: {args.only}", file=sys.stderr)
            return 2

    print(f"Running {len(examples)} LLM smoke tests via provider={args.provider!r}...")
    print(f"  (key loaded from {env_path}, name only — value never printed)")
    print()

    results: list[dict] = []
    for name, code, expected in examples:
        print(f"=== {name} ===")
        r = _run_one(name, code, expected, args.provider)
        results.append(r)
        if r.get("error"):
            print(f"  FAIL: {r['error']}  (took {r['elapsed_s']:.1f}s)")
        else:
            status = "PASS" if r["ok"] else "FAIL"
            print(
                f"  {status}: {r['recipes']} recipes "
                f"({', '.join(r['actual_types'])}); "
                f"expected ⊇ {{{', '.join(r['expected_subset'])}}}; "
                f"took {r['elapsed_s']:.1f}s"
            )
            if r["missing"]:
                print(f"    missing types: {r['missing']}")
        print()

    # Summary
    passed = sum(1 for r in results if r.get("ok"))
    total = len(results)
    total_time = sum(r["elapsed_s"] for r in results)
    print(f"--- Summary ---")
    print(f"  {passed}/{total} passed")
    print(f"  total time: {total_time:.1f}s")
    if results and any(r.get("model") for r in results):
        models = {r["model"] for r in results if r.get("model")}
        print(f"  models used: {sorted(models)}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
