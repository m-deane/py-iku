"""Tests for ``FlowsRepo`` (M7)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from app.store.flows_repo import FlowsRepo


def _flow(name: str = "f") -> dict:
    return {
        "flow_name": name,
        "total_recipes": 0,
        "total_datasets": 0,
        "datasets": [],
        "recipes": [],
    }


def test_save_and_get_round_trip(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)
    record = repo.save(flow=_flow("hello"), name="my-flow", tags=["a", "b"])
    assert record.id
    assert record.name == "my-flow"
    assert record.tags == ["a", "b"]
    fetched = repo.get(record.id)
    assert fetched is not None
    assert fetched.id == record.id
    assert fetched.flow == record.flow
    assert fetched.created_at == record.created_at


def test_get_unknown_id_returns_none(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)
    assert repo.get("does-not-exist") is None


def test_update_modifies_fields(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)
    rec = repo.save(flow=_flow(), name="orig", tags=["x"])
    updated = repo.update(rec.id, name="renamed", tags=["y", "z"])
    assert updated.id == rec.id
    assert updated.name == "renamed"
    assert updated.tags == ["y", "z"]
    assert updated.created_at == rec.created_at
    assert updated.updated_at >= rec.updated_at


def test_update_unknown_id_raises(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)
    with pytest.raises(KeyError):
        repo.update("missing", name="x")


def test_list_pagination_and_cursor(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)
    ids = [repo.save(flow=_flow(f"f{i}"), name=f"f{i}").id for i in range(5)]
    page1, cursor = repo.list(limit=2)
    assert [r.id for r in page1] == ids[:2]
    assert cursor == ids[1]
    page2, cursor2 = repo.list(limit=2, cursor=cursor)
    assert [r.id for r in page2] == ids[2:4]
    assert cursor2 == ids[3]
    page3, cursor3 = repo.list(limit=2, cursor=cursor2)
    assert [r.id for r in page3] == ids[4:5]
    assert cursor3 is None


def test_list_with_unknown_cursor_returns_empty(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)
    repo.save(flow=_flow(), name="a")
    page, cursor = repo.list(limit=10, cursor="not-a-real-id")
    assert page == []
    assert cursor is None


def test_concurrent_writes_do_not_corrupt_index(tmp_path: Path) -> None:
    repo = FlowsRepo(tmp_path)

    def writer() -> None:
        for i in range(20):
            repo.save(flow=_flow(f"t{i}"), name=f"t{i}")

    threads = [threading.Thread(target=writer) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    page, _ = repo.list(limit=1000)
    # 4 threads * 20 saves each = 80 records, all readable.
    assert len(page) == 80
    # All ids unique.
    assert len({r.id for r in page}) == 80


def test_atomic_write_survives_independent_repo_instance(tmp_path: Path) -> None:
    """A new FlowsRepo instance reads what the first one wrote."""
    repo1 = FlowsRepo(tmp_path)
    rec = repo1.save(flow=_flow("persist"), name="persist")
    repo2 = FlowsRepo(tmp_path)
    assert repo2.get(rec.id) is not None


# ---------------------------------------------------------------------------
# Security: path traversal prevention
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_id",
    [
        "../../../etc/passwd",
        "../../secret",
        "/absolute/path",
        "normal/slash",
        "null\x00byte",
        "a" * 65,  # too long
        "",
    ],
)
def test_get_treats_path_traversal_ids_as_not_found(tmp_path: Path, bad_id: str) -> None:
    """flow_id values that look like path traversal must return None (safe 404), not 500."""
    repo = FlowsRepo(tmp_path)
    result = repo.get(bad_id)
    assert result is None


def test_update_rejects_path_traversal_ids(tmp_path: Path) -> None:
    """update() raises KeyError for unsafe ids (mapped to 404 by the route)."""
    repo = FlowsRepo(tmp_path)
    with pytest.raises(KeyError):
        repo.update("../../etc/shadow", name="x")


def test_flow_path_raises_value_error_for_traversal(tmp_path: Path) -> None:
    """_flow_path raises ValueError directly for path-traversal ids."""
    repo = FlowsRepo(tmp_path)
    with pytest.raises(ValueError, match="Invalid flow_id"):
        repo._flow_path("../../etc/passwd")  # noqa: SLF001
