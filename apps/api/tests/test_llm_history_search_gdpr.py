"""Sprint 5 — audit-log search, severity filter, GDPR export & delete."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import UTC, datetime, timedelta

import pytest

from app.deps import get_llm_audit_repo, get_settings
from app.services.gdpr_export import EXPORT_FILES, build_user_export
from app.services.llm_audit import LlmCallRecord


def _seed(repo, *, n: int = 4) -> None:
    base = datetime.now(tz=UTC) - timedelta(minutes=n)
    samples = [
        {
            "user": "you",
            "prompt": "Convert pandas merge to a join recipe",
            "response": "OK — produced JOIN with left join.",
            "cost": 0.01,
            "status": "success",
        },
        {
            "user": "alice",
            "prompt": "How do I rename a column?",
            "response": "Use COLUMN_RENAMER processor.",
            "cost": 1.50,  # warning
            "status": "success",
        },
        {
            "user": "you",
            "prompt": "Filter trades by book",
            "response": "Use FilterOnValue with FULL_STRING match.",
            "cost": 0.02,
            "status": "failure",
        },
        {
            "user": "alice",
            "prompt": "Pivot exposure by commodity",
            "response": "Use PIVOT recipe with notional.",
            "cost": 0.03,
            "status": "success",
        },
    ]
    for i, sample in enumerate(samples[:n]):
        repo.append(
            LlmCallRecord(
                ts=(base + timedelta(seconds=i)).isoformat(),
                mode="llm",
                provider="anthropic",
                model="claude-3-5-sonnet-latest",
                prompt_tokens=1000,
                completion_tokens=500,
                cost_usd=sample["cost"],
                status=sample["status"],
                feature="convert",
                flow_id=f"flow-{i}",
                user=sample["user"],
                prompt=sample["prompt"],
                response=sample["response"],
            )
        )


@pytest.mark.asyncio
async def test_search_q_matches_prompt(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history?q=rename")
    body = resp.json()
    assert resp.status_code == 200
    assert len(body["records"]) == 1
    assert "rename" in body["records"][0]["prompt"].lower()


@pytest.mark.asyncio
async def test_search_q_matches_response(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history?q=PIVOT")
    body = resp.json()
    assert resp.status_code == 200
    assert any("pivot" in r["prompt"].lower() for r in body["records"])


@pytest.mark.asyncio
async def test_filter_by_user(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history?user=alice")
    body = resp.json()
    assert all(r["user"] == "alice" for r in body["records"])
    assert len(body["records"]) == 2


@pytest.mark.asyncio
async def test_user_list_surfaced_for_dropdown(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history")
    body = resp.json()
    assert set(body["users"]) == {"you", "alice"}


@pytest.mark.asyncio
async def test_filter_by_severity_warning(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history?severity=warning")
    body = resp.json()
    assert all(r["severity"] == "warning" for r in body["records"])
    assert all(r["cost_usd"] > 1.0 for r in body["records"])


@pytest.mark.asyncio
async def test_filter_by_severity_error(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history?severity=error")
    body = resp.json()
    assert all(r["severity"] == "error" for r in body["records"])
    assert all(r["status"] == "failure" for r in body["records"])


# ---------------------------------------------------------------------------
# GDPR export
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gdpr_export_returns_zip_with_required_files(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history/export?user=you")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    disposition = resp.headers["content-disposition"]
    assert "py-iku-studio-export-you-" in disposition
    assert disposition.endswith('.zip"')

    with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
        names = set(zf.namelist())
    # Checklist test — every required artefact must be present.
    for required in EXPORT_FILES:
        assert required in names, f"Missing required export file {required}"
    assert "manifest.json" in names


@pytest.mark.asyncio
async def test_gdpr_export_only_includes_target_user_records(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history/export?user=alice")
    with zipfile.ZipFile(io.BytesIO(resp.content), "r") as zf:
        body = zf.read("llm-history.jsonl").decode("utf-8").splitlines()
    assert body, "expected alice's records in the export"
    for line in body:
        rec = json.loads(line)
        assert rec["user"] == "alice"


@pytest.mark.asyncio
async def test_gdpr_export_default_user_when_query_missing(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.get("/llm-history/export")
    assert resp.status_code == 200
    # Default user is "you" when STUDIO_USER env var unset
    assert "py-iku-studio-export-you-" in resp.headers["content-disposition"]


def test_gdpr_export_includes_budget_and_comments(tmp_path) -> None:
    """Bundler picks up budget config + a per-user comment file."""
    from app.services.llm_audit import LlmAuditRepo

    base = tmp_path
    (base / "comments").mkdir()
    (base / "comments" / "11111111-2222-3333-4444-555555555555.jsonl").write_text(
        json.dumps(
            {
                "id": "c1",
                "flow_id": "11111111-2222-3333-4444-555555555555",
                "recipe_id": "r1",
                "author": "alice",
                "body": "looks right",
                "timestamp": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (base / "llm-budget.json").write_text(
        json.dumps({"monthly_cap_usd": 75.0, "per_call_cap_usd": 0.5})
    )

    repo = LlmAuditRepo(base_dir=base)
    repo.append(
        LlmCallRecord(
            ts="2026-01-02T00:00:00+00:00",
            mode="llm",
            provider="anthropic",
            model="claude-3-5-sonnet-latest",
            prompt_tokens=1,
            completion_tokens=1,
            cost_usd=0.0,
            status="success",
            user="alice",
            prompt="hi",
            response="hello",
        )
    )

    zip_bytes, filename = build_user_export(
        base_dir=base, user="alice", audit_repo=repo
    )
    assert filename.startswith("py-iku-studio-export-alice-")

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        comments = zf.read("comments.jsonl").decode("utf-8")
        budget = json.loads(zf.read("budget-config.json").decode("utf-8"))
        history = zf.read("llm-history.jsonl").decode("utf-8")
    assert "alice" in comments
    assert budget["monthly_cap_usd"] == 75.0
    assert "alice" in history


# ---------------------------------------------------------------------------
# GDPR delete
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gdpr_delete_requires_confirmation(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)
    resp = await client.delete("/llm-history?user=alice")
    assert resp.status_code == 400
    assert "confirm" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_gdpr_delete_removes_user_records(client) -> None:  # type: ignore[no-untyped-def]
    repo = get_llm_audit_repo()
    _seed(repo, n=4)

    resp = await client.delete("/llm-history?user=alice&confirm=yes")
    assert resp.status_code == 200
    assert resp.json()["removed"] == 2

    follow = await client.get("/llm-history?user=alice")
    assert follow.json()["records"] == []

    # Other user untouched
    follow_you = await client.get("/llm-history?user=you")
    assert len(follow_you.json()["records"]) == 2
