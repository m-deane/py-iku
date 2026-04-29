"""Corpus runner — POSTs each script in scripts/ to the live /convert endpoint.

This runner DOES NOT import py2dataiku directly; it talks to the running
HTTP API (default http://127.0.0.1:8000/convert) so the runner is decoupled
from the conversion engine version.

Usage:
    python tests/test_llm_corpus/harness/run_corpus.py \
        [--mode rule|llm|both] \
        [--scripts <id1,id2,...>] \
        [--runs N] \
        [--cost-cap USD] \
        [--endpoint URL] \
        [--results-dir PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

try:
    import urllib.request as _urlreq
    import urllib.error as _urlerr
except ImportError:  # pragma: no cover
    raise

CORPUS_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = CORPUS_ROOT / "scripts"
EXPECTED_DIR = CORPUS_ROOT / "expected"
EXPECTED_LLM_DIR = CORPUS_ROOT / "expected_llm"
RESULTS_DIR = CORPUS_ROOT / "results"


def _expected_dir_for(mode: str) -> Path:
    """Return the expected/ directory for the given convert mode.

    Rule mode and LLM mode produce structurally different flows for
    several pandas idioms (compound predicates -> SPLIT vs PREPARE+
    FilterOnFormula; head-after-sort -> sort+sampling vs TOP_N; etc.).
    Each mode has its own pinned expectations.
    """
    return EXPECTED_LLM_DIR if mode == "llm" else EXPECTED_DIR


def _load_expected(script_id: str, mode: str = "rule") -> dict:
    path = _expected_dir_for(mode) / f"{script_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _list_scripts(filter_ids: Optional[List[str]]) -> List[str]:
    all_ids = sorted(p.stem for p in SCRIPTS_DIR.glob("*.py") if not p.name.startswith("_"))
    if not filter_ids:
        return all_ids
    wanted = set(filter_ids)
    return [sid for sid in all_ids if sid in wanted]


def _post_convert(endpoint: str, code: str, mode: str, timeout: float = 120.0) -> dict:
    """POST {code, mode} to /convert and return the parsed JSON response.

    Returns a dict with keys: status_code, body (parsed json or raw text),
    elapsed_seconds, error.
    """
    payload = json.dumps({"code": code, "mode": mode}).encode("utf-8")
    req = _urlreq.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    started = time.monotonic()
    try:
        with _urlreq.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            elapsed = time.monotonic() - started
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"_raw": raw}
            return {
                "status_code": resp.status,
                "body": body,
                "elapsed_seconds": elapsed,
                "error": None,
            }
    except _urlerr.HTTPError as exc:  # noqa: BLE001
        elapsed = time.monotonic() - started
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:  # noqa: BLE001
            body = {"_raw": str(exc)}
        return {
            "status_code": exc.code,
            "body": body,
            "elapsed_seconds": elapsed,
            "error": f"HTTP {exc.code}",
        }
    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - started
        return {
            "status_code": None,
            "body": None,
            "elapsed_seconds": elapsed,
            "error": str(exc),
        }


def _flow_from_response(body: dict) -> dict:
    """Extract the canonical flow dict from various response shapes."""
    if not isinstance(body, dict):
        return {}
    for key in ("flow", "result", "data"):
        v = body.get(key)
        if isinstance(v, dict):
            inner = v.get("flow") if isinstance(v.get("flow"), dict) else v
            if "recipes" in inner or "datasets" in inner:
                return inner
    if "recipes" in body or "datasets" in body:
        return body
    return {}


def _evaluate(expected: dict, body: dict) -> dict:
    """Lightweight pass/fail scoring; deep diff is left to diff_corpus.py."""
    flow = _flow_from_response(body)
    recipes = flow.get("recipes") or []
    datasets = flow.get("datasets") or []
    actual_types = sorted(
        (r.get("type") or r.get("recipe_type") or "").lower() for r in recipes
    )
    expected_types = sorted(t.lower() for t in expected.get("expected_recipe_types", []))
    must_not = {t.lower() for t in expected.get("must_not_contain", [])}

    failures: List[str] = []
    if expected_types and actual_types != expected_types:
        failures.append(
            f"recipe_types: expected={expected_types} actual={actual_types}"
        )
    if must_not & set(actual_types):
        failures.append(f"must_not_contain hit: {sorted(must_not & set(actual_types))}")
    expected_count = expected.get("expected_dataset_count")
    if expected_count is not None and len(datasets) != expected_count:
        failures.append(f"dataset_count: expected={expected_count} actual={len(datasets)}")

    return {
        "pass": not failures,
        "failures": failures,
        "actual_recipe_types": actual_types,
        "actual_dataset_count": len(datasets),
    }


def _extract_cost(body: dict) -> float:
    """Best-effort: pull `cost_usd` or sum from a `usage` dict if present."""
    if not isinstance(body, dict):
        return 0.0
    for key in ("cost_usd", "cost"):
        v = body.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    usage = body.get("usage") if isinstance(body.get("usage"), dict) else None
    if usage and isinstance(usage.get("cost_usd"), (int, float)):
        return float(usage["cost_usd"])
    return 0.0


def run_corpus(
    mode: str = "llm",
    scripts: Optional[List[str]] = None,
    runs: int = 1,
    cost_cap: Optional[float] = None,
    endpoint: str = "http://127.0.0.1:8000/convert",
    results_dir: Path = RESULTS_DIR,
    timeout: float = 120.0,
) -> dict:
    """Run the corpus once. Returns a summary dict."""
    modes: Iterable[str]
    if mode == "both":
        modes = ("rule", "llm")
    elif mode in ("rule", "llm"):
        modes = (mode,)
    else:
        raise ValueError(f"mode must be rule|llm|both, got {mode!r}")

    results_dir.mkdir(parents=True, exist_ok=True)
    script_ids = _list_scripts(scripts)
    if not script_ids:
        print(f"WARN: no scripts matched filter {scripts}", file=sys.stderr)
        return {"runs": [], "total_cost_usd": 0.0, "passed": 0, "failed": 0, "stopped": False}

    total_cost = 0.0
    passed = failed = 0
    stopped = False
    run_records: List[dict] = []

    for run_idx in range(runs):
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
        for sid in script_ids:
            for current_mode in modes:
                if cost_cap is not None and total_cost >= cost_cap:
                    print(f"STOP: cost cap reached (${total_cost:.4f} >= ${cost_cap:.4f})")
                    stopped = True
                    break
                code = (SCRIPTS_DIR / f"{sid}.py").read_text(encoding="utf-8")
                # Use the mode-specific expected file when available
                # (expected_llm/ for LLM mode, expected/ for rule mode).
                # Falls back to the rule expected if a per-mode file is
                # missing — the harness reports the mismatch rather than
                # failing to load.
                try:
                    expected = _load_expected(sid, current_mode)
                except FileNotFoundError:
                    expected = _load_expected(sid, "rule")
                resp = _post_convert(endpoint, code, current_mode, timeout=timeout)
                cost = _extract_cost(resp["body"] if isinstance(resp["body"], dict) else {})
                total_cost += cost
                evaluation = _evaluate(
                    expected, resp["body"] if isinstance(resp["body"], dict) else {}
                )
                record = {
                    "script_id": sid,
                    "mode": current_mode,
                    "run_id": run_id,
                    "run_index": run_idx,
                    "endpoint": endpoint,
                    "status_code": resp["status_code"],
                    "elapsed_seconds": resp["elapsed_seconds"],
                    "cost_usd": cost,
                    "error": resp["error"],
                    "evaluation": evaluation,
                    "response_body": resp["body"],
                    "expected": expected,
                }
                out_path = results_dir / f"{sid}-{current_mode}-{run_id}.json"
                out_path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
                tag = "PASS" if evaluation["pass"] else "FAIL"
                reason = "" if evaluation["pass"] else f" — {'; '.join(evaluation['failures'])}"
                err = f" [error: {resp['error']}]" if resp["error"] else ""
                print(f"{tag} {sid} ({current_mode}) {resp['elapsed_seconds']:.2f}s ${cost:.4f}{reason}{err}")
                run_records.append(record)
                if evaluation["pass"]:
                    passed += 1
                else:
                    failed += 1
            if stopped:
                break
        if stopped:
            break

    print()
    print(f"Total: {passed} passed, {failed} failed, ${total_cost:.4f} spent.")
    return {
        "runs": run_records,
        "total_cost_usd": total_cost,
        "passed": passed,
        "failed": failed,
        "stopped": stopped,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run the py-iku LLM corpus against /convert.")
    parser.add_argument("--mode", choices=["rule", "llm", "both"], default="llm")
    parser.add_argument("--scripts", default=None, help="Comma-separated list of script ids.")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--cost-cap", type=float, default=None)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/convert")
    parser.add_argument("--results-dir", default=str(RESULTS_DIR))
    parser.add_argument("--timeout", type=float, default=120.0)
    args = parser.parse_args(argv)
    scripts_filter = [s.strip() for s in args.scripts.split(",")] if args.scripts else None
    summary = run_corpus(
        mode=args.mode,
        scripts=scripts_filter,
        runs=args.runs,
        cost_cap=args.cost_cap,
        endpoint=args.endpoint,
        results_dir=Path(args.results_dir),
        timeout=args.timeout,
    )
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
