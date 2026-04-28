"""Corpus comparator — produces a markdown diff report from results/.

Reads every results/*.json file produced by run_corpus.py and emits a
markdown matrix at the requested path with:
  - per-script pass/fail
  - recipe-type sequence diff (expected vs actual)
  - dataset-name diff
  - confidence drift (if `confidence` present in response)
  - cost variance across runs

Usage:
    python tests/test_llm_corpus/harness/diff_corpus.py [--report PATH]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CORPUS_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = CORPUS_ROOT / "results"
DEFAULT_REPORT_DIR = Path("/tmp/py-iku-review")


def _load_results(results_dir: Path) -> List[dict]:
    out: List[dict] = []
    for path in sorted(results_dir.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: skipping {path.name}: {exc}", file=sys.stderr)
    return out


def _flow_from_response(body: Any) -> dict:
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


def _seq_diff(expected: List[str], actual: List[str]) -> str:
    e = [t.lower() for t in (expected or [])]
    a = [t.lower() for t in (actual or [])]
    if e == a:
        return "OK"
    return f"expected={sorted(e)} actual={sorted(a)}"


def _dataset_names(flow: dict) -> List[str]:
    return sorted((d.get("name") or "") for d in (flow.get("datasets") or []))


def _confidence(body: Any) -> Optional[float]:
    if not isinstance(body, dict):
        return None
    for key in ("confidence", "overall_confidence"):
        v = body.get(key)
        if isinstance(v, (int, float)):
            return float(v)
    res = body.get("result")
    if isinstance(res, dict):
        v = res.get("confidence")
        if isinstance(v, (int, float)):
            return float(v)
    return None


def build_report(records: List[dict]) -> str:
    """Build a markdown report string from a list of result records."""
    by_script: Dict[str, List[dict]] = defaultdict(list)
    for r in records:
        by_script[r.get("script_id", "?")].append(r)

    out: List[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    out.append(f"# py-iku Corpus Diff Report")
    out.append("")
    out.append(f"_Generated {ts}_")
    out.append(f"_Records: {len(records)} across {len(by_script)} scripts_")
    out.append("")

    # Summary table
    out.append("## Summary matrix")
    out.append("")
    out.append("| Script | Mode | Runs | Pass | Recipe-type diff | Dataset-name diff | Cost variance | Confidence drift |")
    out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for sid in sorted(by_script):
        runs = by_script[sid]
        modes = sorted({r.get("mode", "?") for r in runs})
        for mode in modes:
            mode_runs = [r for r in runs if r.get("mode") == mode]
            n = len(mode_runs)
            n_pass = sum(1 for r in mode_runs if r.get("evaluation", {}).get("pass"))
            costs = [r.get("cost_usd", 0.0) or 0.0 for r in mode_runs]
            cost_var = statistics.pstdev(costs) if len(costs) > 1 else 0.0
            confidences = [_confidence(r.get("response_body")) for r in mode_runs]
            confidences = [c for c in confidences if c is not None]
            conf_drift = (max(confidences) - min(confidences)) if len(confidences) > 1 else 0.0

            # Per-mode-aggregated diffs (use the first run as representative).
            first = mode_runs[0]
            expected = first.get("expected") or {}
            flow = _flow_from_response(first.get("response_body"))
            actual_types = sorted(
                (rec.get("type") or rec.get("recipe_type") or "").lower()
                for rec in (flow.get("recipes") or [])
            )
            seq = _seq_diff(expected.get("expected_recipe_types") or [], actual_types)
            ds_actual = _dataset_names(flow)
            ds_expected = sorted(expected.get("expected_outputs") or [])
            ds_diff = "OK" if not ds_expected or all(d in ds_actual for d in ds_expected) else (
                f"missing={sorted(set(ds_expected) - set(ds_actual))}"
            )
            out.append(
                f"| {sid} | {mode} | {n} | {n_pass}/{n} | {seq} | {ds_diff} | "
                f"${cost_var:.4f} | {conf_drift:.3f} |"
            )

    # Per-script detail
    out.append("")
    out.append("## Per-script detail")
    out.append("")
    for sid in sorted(by_script):
        out.append(f"### {sid}")
        for r in by_script[sid]:
            ev = r.get("evaluation", {})
            tag = "PASS" if ev.get("pass") else "FAIL"
            out.append(
                f"- [{tag}] mode={r.get('mode')} run_id={r.get('run_id')} "
                f"elapsed={r.get('elapsed_seconds', 0):.2f}s cost=${r.get('cost_usd', 0):.4f} "
                f"status={r.get('status_code')}"
            )
            if ev.get("failures"):
                for f in ev["failures"]:
                    out.append(f"  - failure: {f}")
            if r.get("error"):
                out.append(f"  - error: {r['error']}")
        out.append("")

    return "\n".join(out)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Diff & report on py-iku corpus results.")
    default_path = DEFAULT_REPORT_DIR / f"corpus-report-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.md"
    parser.add_argument("--report", default=str(default_path))
    parser.add_argument("--results-dir", default=str(RESULTS_DIR))
    args = parser.parse_args(argv)

    records = _load_results(Path(args.results_dir))
    if not records:
        print(f"No results found in {args.results_dir}", file=sys.stderr)
        return 1
    report = build_report(records)
    out_path = Path(args.report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(f"Wrote {out_path} ({len(records)} records).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
