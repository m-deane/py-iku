"""Regenerate expected/{script_id}.json from the live API's current output.

Reads each script in scripts/, POSTs it to /convert in rule mode, and
overwrites the corresponding expected/{script_id}.json with values
derived from the actual response. Preserves the existing `category`,
`known_issues`, `notes`, and `must_not_contain` fields — only the
behavioral expectations (recipe_types, dataset_count, expected_outputs)
are refreshed.

Usage:
    python tests/test_llm_corpus/harness/regenerate_expected.py [--mode rule|llm]

Defaults to rule mode (deterministic, free). After this runs, a follow-up
`run_corpus.py --mode rule` should produce zero failures.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[1]
SCRIPTS = CORPUS / "scripts"
EXPECTED = CORPUS / "expected"


def post_convert(code: str, mode: str, endpoint: str, timeout: int) -> dict:
    body = json.dumps({"mode": mode, "code": code, "temperature": 0.0}).encode()
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode("utf-8", "replace")[:300]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["rule", "llm"], default="rule")
    ap.add_argument("--endpoint", default="http://127.0.0.1:8000/convert?force=true")
    ap.add_argument("--timeout", type=int, default=60)
    args = ap.parse_args()

    refreshed: list[str] = []
    skipped: list[str] = []
    for script in sorted(SCRIPTS.glob("*.py")):
        sid = script.stem
        exp_path = EXPECTED / f"{sid}.json"
        if not exp_path.exists():
            print(f"  skip {sid}: no expected file", file=sys.stderr)
            skipped.append(sid)
            continue
        existing = json.loads(exp_path.read_text())
        code = script.read_text()
        resp = post_convert(code, args.mode, args.endpoint, args.timeout)
        if "_error" in resp:
            print(f"  skip {sid}: HTTP {resp['_error']}", file=sys.stderr)
            skipped.append(sid)
            continue
        flow = resp.get("flow") or {}
        recipes = flow.get("recipes") or []
        datasets = flow.get("datasets") or []
        outputs = [
            d.get("name", "") for d in datasets if d.get("type") == "output"
        ]
        new_expected = {
            "id": existing["id"],
            "category": existing["category"],
            "expected_recipe_types": sorted([r.get("type") for r in recipes]),
            "expected_dataset_count": len(datasets),
            "expected_outputs": sorted(outputs),
            "must_not_contain": existing.get("must_not_contain", []),
            "known_issues": existing.get("known_issues", []),
            "notes": existing.get("notes", ""),
        }
        exp_path.write_text(json.dumps(new_expected, indent=2) + "\n")
        refreshed.append(sid)
        print(f"  refreshed {sid}: {len(recipes)}r/{len(datasets)}d")

    print(f"\nRefreshed {len(refreshed)}; skipped {len(skipped)}")
    if skipped:
        print(f"Skipped ids: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
