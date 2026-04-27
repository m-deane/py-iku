"""Real-LLM smoke test for py-iku **Studio** (FastAPI surface).

Mirrors the pattern in ``scripts/llm_smoke_test.py`` but exercises the
HTTP API rather than the underlying py2dataiku library directly. Useful
when you've changed something in ``apps/api/app/`` and want a one-shot
real-network sanity check before pushing.

Two modes:

* ``--mode in-process`` (default) — imports the FastAPI ASGI app and
  hits it via ``httpx.AsyncClient(transport=ASGITransport(...))``. No
  uvicorn server needed.
* ``--mode http`` — assumes the API is already running and POSTs to
  ``--base-url`` (default ``http://localhost:8000``).

Reads ``ANTHROPIC_API_KEY`` from ``.env.local`` (gitignored). The key
lives in this process's environ ONLY for the duration of the run.

Usage:
    python scripts/studio_smoke_test.py
    python scripts/studio_smoke_test.py --mode http --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> dict[str, str]:
    """Tiny KEY=value parser. No deps, no quoting, no shell interpolation."""
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (
            v.startswith("'") and v.endswith("'")
        ):
            v = v[1:-1]
        if k:
            out[k] = v
    return out


SMOKE_CODE = """\
import pandas as pd
df = pd.read_csv('sales.csv')
df = df.dropna()
result = df.groupby('category').agg({'amount': 'sum'})
"""


async def _run_in_process() -> int:
    """Drive the FastAPI app directly via ASGI transport."""
    # Late import — the API package only resolves once cwd is repo root.
    sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
    from httpx import ASGITransport, AsyncClient  # noqa: WPS433

    from app.main import app  # noqa: WPS433

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver", timeout=60.0
    ) as client:
        return await _exec_smoke(client)


async def _run_http(base_url: str) -> int:
    """POST against an already-running uvicorn server."""
    from httpx import AsyncClient  # noqa: WPS433

    async with AsyncClient(base_url=base_url, timeout=60.0) as client:
        return await _exec_smoke(client)


async def _exec_smoke(client: Any) -> int:
    """Run /convert?mode=llm followed by /chat. Returns exit code (0=ok)."""
    print(f"[1/2] POST /convert?mode=llm  (code: {len(SMOKE_CODE)} bytes)")
    t0 = time.perf_counter()
    resp = await client.post(
        "/convert", json={"code": SMOKE_CODE, "mode": "llm"}
    )
    dt = time.perf_counter() - t0
    if resp.status_code != 200:
        print(f"  FAIL ({dt:.1f}s): status={resp.status_code}\n  body={resp.text[:600]}")
        return 1
    body = resp.json()
    flow = body["flow"]
    score = body["score"]
    recipes = flow.get("recipes") or []
    cost = score.get("cost_estimate")
    print(
        f"  PASS ({dt:.1f}s): recipes={len(recipes)} "
        f"datasets={len(flow.get('datasets') or [])} cost=${cost:.4f}"
    )
    if not recipes or not cost or cost <= 0:
        print("  ERROR: empty flow or zero cost — LLM path may have fallen back")
        return 1

    print("[2/2] POST /chat  (about the first recipe)")
    t0 = time.perf_counter()
    chat_resp = await client.post(
        "/chat",
        json={
            "flow_json": flow,
            "question": (
                "Briefly describe the first recipe in this flow and cite it "
                "with the [recipe:NAME] marker."
            ),
            "provider": "anthropic",
            "stream": False,
        },
    )
    dt = time.perf_counter() - t0
    if chat_resp.status_code != 200:
        print(f"  FAIL ({dt:.1f}s): status={chat_resp.status_code}\n  body={chat_resp.text[:600]}")
        return 1
    chat_body = chat_resp.json()
    print(
        f"  PASS ({dt:.1f}s): answer_chars={len(chat_body.get('answer') or '')} "
        f"citations={len(chat_body.get('citations') or [])} "
        f"cost=${chat_body.get('cost_usd', 0):.4f}"
    )

    print("\n--- Summary ---")
    print(f"  Smoke OK in {dt:.1f}s wall time.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("in-process", "http"), default="in-process")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument(
        "--env-file", default=str(REPO_ROOT / ".env.local"),
        help="Path to .env.local (default: <repo>/.env.local)",
    )
    args = parser.parse_args()

    file_env = _load_env_file(Path(args.env_file))
    key: Optional[str] = file_env.get("ANTHROPIC_API_KEY") or os.environ.get(
        "ANTHROPIC_API_KEY"
    )
    if not key:
        print(
            "ERROR: no ANTHROPIC_API_KEY found.\n"
            f"  - Edit {args.env_file} and add: ANTHROPIC_API_KEY=<your-key>\n"
            "  - Or export it in your shell.\n",
            file=sys.stderr,
        )
        return 2
    os.environ["ANTHROPIC_API_KEY"] = key

    print(f"Studio smoke (mode={args.mode}; key loaded from {args.env_file})")
    print()
    if args.mode == "in-process":
        return asyncio.run(_run_in_process())
    return asyncio.run(_run_http(args.base_url))


if __name__ == "__main__":
    sys.exit(main())
