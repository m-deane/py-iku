"""Tests for DataFlowTracker."""

import pytest

from py2dataiku.parser.dataflow_tracker import DataFlowTracker, DataFrameState


@pytest.fixture
def tracker():
    return DataFlowTracker()


# ---------------------------------------------------------------------------
# register_read
# ---------------------------------------------------------------------------

class TestRegisterRead:
    """Tests for DataFlowTracker.register_read()."""

    def test_register_read_creates_state(self, tracker):
        tracker.register_read("df", "data.csv")
        state = tracker.get_state("df")
        assert state is not None
        assert state.variable_name == "df"

    def test_register_read_stores_source(self, tracker):
        tracker.register_read("df", "data.csv")
        assert tracker.get_source("df") == "data.csv"

    def test_register_read_stores_columns(self, tracker):
        tracker.register_read("df", "data.csv", columns=["id", "name", "value"])
        cols = tracker.get_columns("df")
        assert cols == ["id", "name", "value"]

    def test_register_read_without_columns_is_empty(self, tracker):
        tracker.register_read("df", "data.csv")
        assert tracker.get_columns("df") == []

    def test_register_read_stores_line_number(self, tracker):
        tracker.register_read("df", "data.csv", line=42)
        state = tracker.get_state("df")
        assert state.line_number == 42

    def test_register_read_multiple_variables(self, tracker):
        tracker.register_read("df1", "a.csv")
        tracker.register_read("df2", "b.csv")
        assert tracker.get_source("df1") == "a.csv"
        assert tracker.get_source("df2") == "b.csv"

    def test_register_read_overwrites_existing_state(self, tracker):
        tracker.register_read("df", "old.csv")
        tracker.register_read("df", "new.csv")
        assert tracker.get_source("df") == "new.csv"


# ---------------------------------------------------------------------------
# register_transformation
# ---------------------------------------------------------------------------

class TestRegisterTransformation:
    """Tests for DataFlowTracker.register_transformation()."""

    def test_transformation_creates_target_state(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a", "b"])
        tracker.register_transformation("df", "df2", "dropna")
        state = tracker.get_state("df2")
        assert state is not None

    def test_transformation_copies_columns(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a", "b", "c"])
        tracker.register_transformation("df", "clean_df", "dropna")
        assert tracker.get_columns("clean_df") == ["a", "b", "c"]

    def test_transformation_preserves_source(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_transformation("df", "df2", "dropna")
        assert tracker.get_source("df2") == "data.csv"

    def test_transformation_records_operation(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_transformation("df", "df2", "dropna")
        lineage = tracker.get_lineage("df2")
        assert "dropna" in lineage

    def test_transformation_from_unknown_source_does_nothing(self, tracker):
        tracker.register_transformation("nonexistent", "df2", "dropna")
        assert tracker.get_state("df2") is None

    def test_transformation_with_same_source_and_target(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a"])
        tracker.register_transformation("df", "df", "dropna")
        state = tracker.get_state("df")
        assert state is not None

    def test_transformation_creates_alias(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_transformation("df", "df2", "filter")
        # df2 should be aliased to df (different source and target)
        assert "df2" in tracker.aliases

    def test_chained_transformations_accumulate_lineage(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_transformation("df", "df2", "dropna")
        tracker.register_transformation("df2", "df3", "rename")
        lineage = tracker.get_lineage("df3")
        assert "dropna" in lineage
        assert "rename" in lineage


# ---------------------------------------------------------------------------
# register_column_add
# ---------------------------------------------------------------------------

class TestRegisterColumnAdd:
    """Tests for DataFlowTracker.register_column_add()."""

    def test_column_add_appends_column(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a"])
        tracker.register_column_add("df", "new_col")
        assert "new_col" in tracker.get_columns("df")

    def test_column_add_records_transformation(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_column_add("df", "new_col")
        lineage = tracker.get_lineage("df")
        assert any("add_column" in t for t in lineage)

    def test_column_add_does_not_duplicate_column(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a"])
        tracker.register_column_add("df", "a")  # already exists
        cols = tracker.get_columns("df")
        assert cols.count("a") == 1

    def test_column_add_on_unknown_variable_does_nothing(self, tracker):
        tracker.register_column_add("unknown", "col")  # should not raise
        assert tracker.get_state("unknown") is None


# ---------------------------------------------------------------------------
# register_column_drop
# ---------------------------------------------------------------------------

class TestRegisterColumnDrop:
    """Tests for DataFlowTracker.register_column_drop()."""

    def test_column_drop_removes_column(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a", "b", "c"])
        tracker.register_column_drop("df", ["b"])
        assert "b" not in tracker.get_columns("df")
        assert "a" in tracker.get_columns("df")

    def test_column_drop_multiple_columns(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a", "b", "c", "d"])
        tracker.register_column_drop("df", ["b", "c"])
        cols = tracker.get_columns("df")
        assert "b" not in cols
        assert "c" not in cols
        assert "a" in cols
        assert "d" in cols

    def test_column_drop_records_transformation(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a", "b"])
        tracker.register_column_drop("df", ["b"])
        lineage = tracker.get_lineage("df")
        assert any("drop_columns" in t for t in lineage)

    def test_column_drop_nonexistent_column_is_safe(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a"])
        tracker.register_column_drop("df", ["z"])  # z doesn't exist
        assert tracker.get_columns("df") == ["a"]

    def test_column_drop_on_unknown_variable_does_nothing(self, tracker):
        tracker.register_column_drop("unknown", ["col"])  # should not raise


# ---------------------------------------------------------------------------
# register_column_rename
# ---------------------------------------------------------------------------

class TestRegisterColumnRename:
    """Tests for DataFlowTracker.register_column_rename()."""

    def test_column_rename_updates_name(self, tracker):
        tracker.register_read("df", "data.csv", columns=["old_name", "b"])
        tracker.register_column_rename("df", {"old_name": "new_name"})
        cols = tracker.get_columns("df")
        assert "new_name" in cols
        assert "old_name" not in cols

    def test_column_rename_multiple_columns(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a", "b", "c"])
        tracker.register_column_rename("df", {"a": "x", "b": "y"})
        cols = tracker.get_columns("df")
        assert "x" in cols
        assert "y" in cols
        assert "c" in cols
        assert "a" not in cols

    def test_column_rename_records_transformation(self, tracker):
        tracker.register_read("df", "data.csv", columns=["old"])
        tracker.register_column_rename("df", {"old": "new"})
        lineage = tracker.get_lineage("df")
        assert any("rename" in t for t in lineage)

    def test_column_rename_nonexistent_column_is_safe(self, tracker):
        tracker.register_read("df", "data.csv", columns=["a"])
        tracker.register_column_rename("df", {"z": "w"})
        assert tracker.get_columns("df") == ["a"]

    def test_column_rename_on_unknown_variable_does_nothing(self, tracker):
        tracker.register_column_rename("unknown", {"a": "b"})  # should not raise


# ---------------------------------------------------------------------------
# register_merge
# ---------------------------------------------------------------------------

class TestRegisterMerge:
    """Tests for DataFlowTracker.register_merge()."""

    def test_merge_creates_target_state(self, tracker):
        tracker.register_read("left", "left.csv", columns=["id", "a"])
        tracker.register_read("right", "right.csv", columns=["id", "b"])
        tracker.register_merge("left", "right", "merged", on=["id"])
        assert tracker.get_state("merged") is not None

    def test_merge_combines_columns(self, tracker):
        tracker.register_read("left", "left.csv", columns=["id", "a"])
        tracker.register_read("right", "right.csv", columns=["id", "b"])
        tracker.register_merge("left", "right", "merged", on=["id"])
        cols = tracker.get_columns("merged")
        assert "id" in cols
        assert "a" in cols
        assert "b" in cols

    def test_merge_records_operation_in_lineage(self, tracker):
        tracker.register_read("left", "left.csv", columns=["id"])
        tracker.register_read("right", "right.csv", columns=["id"])
        tracker.register_merge("left", "right", "merged")
        lineage = tracker.get_lineage("merged")
        assert any("merge" in t for t in lineage)

    def test_merge_records_source_description(self, tracker):
        tracker.register_read("df1", "a.csv", columns=["id"])
        tracker.register_read("df2", "b.csv", columns=["id"])
        tracker.register_merge("df1", "df2", "result")
        source = tracker.get_source("result")
        assert "df1" in source
        assert "df2" in source

    def test_merge_with_unknown_left_still_creates_state(self, tracker):
        tracker.register_read("right", "right.csv", columns=["b"])
        tracker.register_merge("unknown_left", "right", "merged")
        assert tracker.get_state("merged") is not None


# ---------------------------------------------------------------------------
# get_columns / get_lineage / get_source / get_state
# ---------------------------------------------------------------------------

class TestGetters:
    """Tests for get_columns(), get_lineage(), get_source(), get_state()."""

    def test_get_columns_for_unknown_returns_empty(self, tracker):
        assert tracker.get_columns("nonexistent") == []

    def test_get_lineage_for_unknown_returns_empty(self, tracker):
        assert tracker.get_lineage("nonexistent") == []

    def test_get_source_for_unknown_returns_none(self, tracker):
        assert tracker.get_source("nonexistent") is None

    def test_get_state_returns_dataframe_state_instance(self, tracker):
        tracker.register_read("df", "data.csv")
        state = tracker.get_state("df")
        assert isinstance(state, DataFrameState)

    def test_get_state_for_unknown_returns_none(self, tracker):
        assert tracker.get_state("nonexistent") is None


# ---------------------------------------------------------------------------
# resolve_alias
# ---------------------------------------------------------------------------

class TestResolveAlias:
    """Tests for DataFlowTracker.resolve_alias()."""

    def test_resolve_nonaliased_variable_returns_itself(self, tracker):
        tracker.register_read("df", "data.csv")
        assert tracker.resolve_alias("df") == "df"

    def test_resolve_aliased_variable(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_transformation("df", "df2", "filter")
        # df2 is aliased to df
        resolved = tracker.resolve_alias("df2")
        assert resolved == "df"

    def test_resolve_unknown_variable_returns_itself(self, tracker):
        assert tracker.resolve_alias("unknown") == "unknown"

    def test_resolve_chain_of_aliases(self, tracker):
        tracker.register_read("df", "data.csv")
        tracker.register_transformation("df", "df2", "filter")
        tracker.register_transformation("df2", "df3", "dropna")
        # df3 -> df2 -> df
        resolved = tracker.resolve_alias("df3")
        assert resolved == "df"
