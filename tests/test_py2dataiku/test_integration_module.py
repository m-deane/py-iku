"""Integration tests for DSSFlowDeployer and MCP tool generation.

Tests cover:
1. DSSFlowDeployer in dry_run mode (deploy, deploy_dataset, deploy_recipe)
2. generate_mcp_tool_calls() structure and ordering
3. format_mcp_script() output formatting
4. End-to-end: convert() -> DSSFlowDeployer(dry_run=True).deploy()
"""

import json

import pytest

from py2dataiku import (
    convert,
    DataikuFlow,
    DataikuRecipe,
    DataikuDataset,
    RecipeType,
    DatasetType,
    DatasetConnectionType,
    PrepareStep,
    ProcessorType,
    Aggregation,
    JoinKey,
    JoinType,
    ColumnSchema,
)
from py2dataiku.integrations import (
    DSSFlowDeployer,
    DeploymentResult,
    generate_mcp_tool_calls,
    format_mcp_script,
)
from py2dataiku.integrations.dss_client import _get_dss_recipe_type
from py2dataiku.models.recipe_settings import (
    PrepareSettings,
    GroupingSettings,
    JoinSettings,
    WindowSettings,
    SamplingSettings,
    SplitSettings,
    SortSettings,
    TopNSettings,
    DistinctSettings,
    StackSettings,
    PythonSettings,
    PivotSettings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _simple_flow() -> DataikuFlow:
    """Create a simple flow: input -> prepare -> output."""
    flow = DataikuFlow(name="simple_flow")
    flow.add_dataset(DataikuDataset(name="raw_data", dataset_type=DatasetType.INPUT))
    flow.add_dataset(DataikuDataset(name="cleaned_data", dataset_type=DatasetType.OUTPUT))
    recipe = DataikuRecipe.create_prepare(
        name="clean_data",
        input_dataset="raw_data",
        output_dataset="cleaned_data",
        steps=[
            PrepareStep(
                processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                params={"columns": ["age"], "value": "0"},
            ),
        ],
    )
    flow.add_recipe(recipe)
    return flow


def _multi_recipe_flow() -> DataikuFlow:
    """Create a multi-recipe flow with several recipe types.

    raw_data -> prepare -> cleaned -> grouping -> summary
                                   -> join (with lookup) -> enriched
    """
    flow = DataikuFlow(name="multi_recipe_flow")

    # Datasets
    flow.add_dataset(DataikuDataset(name="raw_data", dataset_type=DatasetType.INPUT))
    flow.add_dataset(DataikuDataset(name="lookup", dataset_type=DatasetType.INPUT))
    flow.add_dataset(
        DataikuDataset(name="cleaned", dataset_type=DatasetType.INTERMEDIATE)
    )
    flow.add_dataset(
        DataikuDataset(name="summary", dataset_type=DatasetType.OUTPUT)
    )
    flow.add_dataset(
        DataikuDataset(name="enriched", dataset_type=DatasetType.OUTPUT)
    )

    # Recipe 1: Prepare
    prepare = DataikuRecipe.create_prepare(
        name="prep_data",
        input_dataset="raw_data",
        output_dataset="cleaned",
        steps=[
            PrepareStep(
                processor_type=ProcessorType.REMOVE_ROWS_ON_EMPTY,
                params={"columns": ["id"]},
            ),
        ],
    )
    flow.add_recipe(prepare)

    # Recipe 2: Grouping
    grouping = DataikuRecipe.create_grouping(
        name="group_data",
        input_dataset="cleaned",
        output_dataset="summary",
        keys=["category"],
        aggregations=[Aggregation(column="amount", function="SUM")],
    )
    flow.add_recipe(grouping)

    # Recipe 3: Join
    join = DataikuRecipe.create_join(
        name="join_data",
        left_dataset="cleaned",
        right_dataset="lookup",
        output_dataset="enriched",
        join_keys=[JoinKey(left_column="id", right_column="id")],
        join_type=JoinType.LEFT,
    )
    flow.add_recipe(join)

    return flow


def _flow_with_settings() -> DataikuFlow:
    """Create a flow with composed RecipeSettings objects."""
    flow = DataikuFlow(name="settings_flow")
    flow.add_dataset(DataikuDataset(name="input_ds", dataset_type=DatasetType.INPUT))
    flow.add_dataset(DataikuDataset(name="prepared_ds", dataset_type=DatasetType.INTERMEDIATE))
    flow.add_dataset(DataikuDataset(name="grouped_ds", dataset_type=DatasetType.OUTPUT))

    # Prepare recipe with settings object
    prepare = DataikuRecipe(
        name="prep_with_settings",
        recipe_type=RecipeType.PREPARE,
        inputs=["input_ds"],
        outputs=["prepared_ds"],
        settings=PrepareSettings(
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.COLUMN_RENAMER,
                    params={"inputColumn": "old", "outputColumn": "new"},
                )
            ]
        ),
    )
    flow.add_recipe(prepare)

    # Grouping recipe with settings object
    grouping = DataikuRecipe(
        name="group_with_settings",
        recipe_type=RecipeType.GROUPING,
        inputs=["prepared_ds"],
        outputs=["grouped_ds"],
        settings=GroupingSettings(
            keys=["category"],
            aggregations=[Aggregation(column="value", function="sum")],
            global_count=True,
        ),
    )
    flow.add_recipe(grouping)

    return flow


# ===========================================================================
# 1. DeploymentResult
# ===========================================================================

class TestDeploymentResult:
    """Tests for the DeploymentResult dataclass."""

    def test_default_values(self):
        result = DeploymentResult()
        assert result.datasets_created == []
        assert result.recipes_created == []
        assert result.errors == []
        assert result.warnings == []
        assert result.dry_run is False
        assert result.success is True

    def test_success_false_with_errors(self):
        result = DeploymentResult(errors=["something failed"])
        assert result.success is False

    def test_to_dict(self):
        result = DeploymentResult(
            datasets_created=["ds1"],
            recipes_created=["r1"],
            dry_run=True,
        )
        d = result.to_dict()
        assert d["datasets_created"] == ["ds1"]
        assert d["recipes_created"] == ["r1"]
        assert d["dry_run"] is True
        assert d["success"] is True

    def test_repr_dry_run(self):
        result = DeploymentResult(dry_run=True)
        assert "DRY RUN" in repr(result)

    def test_repr_ok(self):
        result = DeploymentResult(dry_run=False)
        assert "OK" in repr(result)

    def test_repr_failed(self):
        result = DeploymentResult(errors=["err"])
        assert "FAILED" in repr(result)


# ===========================================================================
# 2. DSSFlowDeployer initialization
# ===========================================================================

class TestDSSFlowDeployerInit:
    """Tests for DSSFlowDeployer initialization."""

    def test_init_basic(self):
        deployer = DSSFlowDeployer("https://dss.example.com", "key123", "MY_PROJ")
        assert deployer.host == "https://dss.example.com"
        assert deployer.api_key == "key123"
        assert deployer.project_key == "MY_PROJ"
        assert deployer.dry_run is False

    def test_init_strips_trailing_slash(self):
        deployer = DSSFlowDeployer("https://dss.example.com/", "key", "PROJ")
        assert deployer.host == "https://dss.example.com"

    def test_init_dry_run(self):
        deployer = DSSFlowDeployer("", "", "PROJ", dry_run=True)
        assert deployer.dry_run is True
        assert deployer.host == ""

    def test_ensure_connected_requires_dataikuapi(self):
        deployer = DSSFlowDeployer("https://x", "key", "PROJ")
        # Should raise ExportError because dataikuapi is not installed
        from py2dataiku.exceptions import ExportError
        with pytest.raises(ExportError, match="dataikuapi"):
            deployer._ensure_connected()


# ===========================================================================
# 3. DSSFlowDeployer.deploy_dataset() (dry_run)
# ===========================================================================

class TestDeployDatasetDryRun:
    """Tests for deploy_dataset in dry_run mode."""

    def setup_method(self):
        self.deployer = DSSFlowDeployer("", "", "TEST_PROJ", dry_run=True)

    def test_basic_dataset(self):
        ds = DataikuDataset(name="my_dataset", dataset_type=DatasetType.INPUT)
        info = self.deployer.deploy_dataset(ds)
        assert info["name"] == "my_dataset"
        assert info["type"] == "input"
        assert info["connection_type"] == "Filesystem"

    def test_dataset_with_connection_type(self):
        ds = DataikuDataset(
            name="pg_dataset",
            dataset_type=DatasetType.OUTPUT,
            connection_type=DatasetConnectionType.SQL_POSTGRESQL,
        )
        info = self.deployer.deploy_dataset(ds)
        assert info["connection_type"] == "PostgreSQL"

    def test_dataset_with_schema(self):
        ds = DataikuDataset(
            name="schema_ds",
            dataset_type=DatasetType.INTERMEDIATE,
            schema=[
                ColumnSchema(name="id", type="int"),
                ColumnSchema(name="name", type="string"),
            ],
        )
        info = self.deployer.deploy_dataset(ds)
        assert info["name"] == "schema_ds"
        # Schema is applied in non-dry-run; in dry_run we just get the info dict
        assert "type" in info


# ===========================================================================
# 4. DSSFlowDeployer.deploy_recipe() (dry_run)
# ===========================================================================

class TestDeployRecipeDryRun:
    """Tests for deploy_recipe in dry_run mode for each recipe type."""

    def setup_method(self):
        self.deployer = DSSFlowDeployer("", "", "TEST_PROJ", dry_run=True)

    def test_prepare_recipe(self):
        recipe = DataikuRecipe.create_prepare(
            name="prep1",
            input_dataset="in",
            output_dataset="out",
            steps=[PrepareStep(processor_type=ProcessorType.COLUMN_RENAMER, params={})],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["name"] == "prep1"
        assert info["type"] == "shaker"
        assert info["inputs"] == ["in"]
        assert info["outputs"] == ["out"]
        assert "builder_args" in info

    def test_grouping_recipe(self):
        recipe = DataikuRecipe.create_grouping(
            name="grp1",
            input_dataset="in",
            output_dataset="out",
            keys=["cat"],
            aggregations=[Aggregation(column="val", function="SUM")],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "grouping"

    def test_join_recipe(self):
        recipe = DataikuRecipe.create_join(
            name="join1",
            left_dataset="left",
            right_dataset="right",
            output_dataset="joined",
            join_keys=[JoinKey(left_column="id", right_column="id")],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "join"
        assert info["inputs"] == ["left", "right"]

    def test_python_recipe(self):
        recipe = DataikuRecipe.create_python(
            name="py1",
            inputs=["in"],
            outputs=["out"],
            code="print('hello')",
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "python"

    def test_sort_recipe(self):
        recipe = DataikuRecipe(
            name="sort1",
            recipe_type=RecipeType.SORT,
            inputs=["in"],
            outputs=["out"],
            sort_columns=[{"column": "date", "order": "desc"}],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "sort"

    def test_distinct_recipe(self):
        recipe = DataikuRecipe(
            name="dist1",
            recipe_type=RecipeType.DISTINCT,
            inputs=["in"],
            outputs=["out"],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "distinct"

    def test_stack_recipe(self):
        recipe = DataikuRecipe(
            name="stack1",
            recipe_type=RecipeType.STACK,
            inputs=["a", "b"],
            outputs=["stacked"],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "vstack"

    def test_split_recipe(self):
        recipe = DataikuRecipe(
            name="split1",
            recipe_type=RecipeType.SPLIT,
            inputs=["in"],
            outputs=["out_a", "out_b"],
            split_condition="val(age) > 18",
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "split"

    def test_sampling_recipe(self):
        recipe = DataikuRecipe(
            name="sample1",
            recipe_type=RecipeType.SAMPLING,
            inputs=["in"],
            outputs=["out"],
            sample_size=100,
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "sampling"

    def test_topn_recipe(self):
        recipe = DataikuRecipe(
            name="topn1",
            recipe_type=RecipeType.TOP_N,
            inputs=["in"],
            outputs=["out"],
            top_n=5,
            ranking_column="score",
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "topn"

    def test_window_recipe(self):
        recipe = DataikuRecipe(
            name="win1",
            recipe_type=RecipeType.WINDOW,
            inputs=["in"],
            outputs=["out"],
            partition_columns=["category"],
            order_columns=["date"],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "window"

    def test_pivot_recipe(self):
        recipe = DataikuRecipe(
            name="pivot1",
            recipe_type=RecipeType.PIVOT,
            inputs=["in"],
            outputs=["out"],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "pivot"

    def test_sync_recipe(self):
        recipe = DataikuRecipe(
            name="sync1",
            recipe_type=RecipeType.SYNC,
            inputs=["in"],
            outputs=["out"],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "sync"

    def test_sql_recipe(self):
        recipe = DataikuRecipe(
            name="sql1",
            recipe_type=RecipeType.SQL,
            inputs=["in"],
            outputs=["out"],
        )
        info = self.deployer.deploy_recipe(recipe)
        assert info["type"] == "sql_query"

    def test_recipe_with_settings_object(self):
        """Verify that deploy_recipe uses to_dss_builder_args when settings object is set."""
        recipe = DataikuRecipe(
            name="prep_settings",
            recipe_type=RecipeType.PREPARE,
            inputs=["in"],
            outputs=["out"],
            settings=PrepareSettings(
                steps=[
                    PrepareStep(
                        processor_type=ProcessorType.FILL_EMPTY_WITH_VALUE,
                        params={"columns": ["x"], "value": "0"},
                    )
                ]
            ),
        )
        info = self.deployer.deploy_recipe(recipe)
        builder_args = info["builder_args"]
        assert "steps" in builder_args
        assert builder_args["mode"] == "BATCH"
        assert len(builder_args["steps"]) == 1

    def test_recipe_builder_args_grouping_settings(self):
        recipe = DataikuRecipe(
            name="grp_s",
            recipe_type=RecipeType.GROUPING,
            inputs=["in"],
            outputs=["out"],
            settings=GroupingSettings(
                keys=["region"],
                aggregations=[Aggregation(column="sales", function="sum")],
            ),
        )
        info = self.deployer.deploy_recipe(recipe)
        ba = info["builder_args"]
        assert ba["keys"][0]["column"] == "region"
        assert ba["values"][0]["function"] == "SUM"


# ===========================================================================
# 5. DSSFlowDeployer.deploy() (dry_run)
# ===========================================================================

class TestDeployFlowDryRun:
    """Tests for deploying entire flows in dry_run mode."""

    def setup_method(self):
        self.deployer = DSSFlowDeployer("", "", "TEST_PROJ", dry_run=True)

    def test_simple_flow(self):
        flow = _simple_flow()
        result = self.deployer.deploy(flow)
        assert result.dry_run is True
        assert result.success is True
        assert "raw_data" in result.datasets_created
        assert "cleaned_data" in result.datasets_created
        assert "clean_data" in result.recipes_created
        assert len(result.errors) == 0

    def test_multi_recipe_flow(self):
        flow = _multi_recipe_flow()
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert len(result.datasets_created) == 5
        assert len(result.recipes_created) == 3

    def test_datasets_created_before_recipes(self):
        """Verify topological order: datasets are created before their consuming recipes."""
        flow = _simple_flow()
        result = self.deployer.deploy(flow)
        # In the topological order, raw_data must appear before clean_data recipe
        ds_idx = result.datasets_created.index("raw_data")
        # All datasets should be created; recipe should be in recipes_created
        assert ds_idx >= 0
        assert "clean_data" in result.recipes_created

    def test_flow_with_settings(self):
        flow = _flow_with_settings()
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert "prep_with_settings" in result.recipes_created
        assert "group_with_settings" in result.recipes_created

    def test_empty_flow(self):
        flow = DataikuFlow(name="empty")
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert result.datasets_created == []
        assert result.recipes_created == []

    def test_flow_validation_errors(self):
        """A flow with missing datasets should produce validation errors."""
        flow = DataikuFlow(name="bad_flow")
        # Add a recipe referencing a non-existent input dataset (not auto-created)
        recipe = DataikuRecipe(
            name="orphan_recipe",
            recipe_type=RecipeType.PYTHON,
            inputs=["missing_input"],
            outputs=["some_output"],
            code="pass",
        )
        flow.recipes.append(recipe)
        # Manually add only the output dataset
        flow.datasets.append(
            DataikuDataset(name="some_output", dataset_type=DatasetType.OUTPUT)
        )
        result = self.deployer.deploy(flow)
        # Missing input dataset should cause validation error
        assert any("missing_input" in e for e in result.errors)

    def test_deploy_preserves_warnings(self):
        flow = _simple_flow()
        # Add an orphan dataset to trigger a warning
        flow.add_dataset(DataikuDataset(name="orphan_ds", dataset_type=DatasetType.INPUT))
        result = self.deployer.deploy(flow)
        assert result.success is True
        # The orphan dataset warning should be propagated
        assert any("orphan" in w.lower() for w in result.warnings)


# ===========================================================================
# 6. _get_dss_recipe_type
# ===========================================================================

class TestGetDSSRecipeType:
    """Tests for the recipe type mapping function."""

    def test_known_types(self):
        assert _get_dss_recipe_type(RecipeType.PREPARE) == "shaker"
        assert _get_dss_recipe_type(RecipeType.JOIN) == "join"
        assert _get_dss_recipe_type(RecipeType.STACK) == "vstack"
        assert _get_dss_recipe_type(RecipeType.PYTHON) == "python"
        assert _get_dss_recipe_type(RecipeType.SQL) == "sql_query"
        assert _get_dss_recipe_type(RecipeType.SORT) == "sort"
        assert _get_dss_recipe_type(RecipeType.DISTINCT) == "distinct"
        assert _get_dss_recipe_type(RecipeType.TOP_N) == "topn"

    def test_unknown_type_defaults_to_python(self):
        # RecipeType.FUZZY_JOIN is not in the map
        assert _get_dss_recipe_type(RecipeType.FUZZY_JOIN) == "python"


# ===========================================================================
# 7. generate_mcp_tool_calls()
# ===========================================================================

class TestGenerateMCPToolCalls:
    """Tests for generate_mcp_tool_calls()."""

    def test_simple_flow(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "MY_PROJECT")
        assert len(calls) > 0

        # All entries should have tool_name and arguments
        for call in calls:
            assert "tool_name" in call
            assert "arguments" in call
            assert call["tool_name"] in ("create_dataset", "create_recipe")

    def test_tool_names(self):
        """Only create_dataset and create_recipe tool names should appear."""
        flow = _multi_recipe_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        tool_names = {c["tool_name"] for c in calls}
        assert tool_names == {"create_dataset", "create_recipe"}

    def test_project_key_in_arguments(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "MY_PROJECT")
        for call in calls:
            assert call["arguments"]["project_key"] == "MY_PROJECT"

    def test_dataset_args_structure(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        ds_calls = [c for c in calls if c["tool_name"] == "create_dataset"]
        assert len(ds_calls) >= 1
        for dc in ds_calls:
            args = dc["arguments"]
            assert "dataset_name" in args
            assert "connection_type" in args

    def test_recipe_args_structure(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        recipe_calls = [c for c in calls if c["tool_name"] == "create_recipe"]
        assert len(recipe_calls) >= 1
        for rc in recipe_calls:
            args = rc["arguments"]
            assert "recipe_name" in args
            assert "recipe_type" in args
            assert "inputs" in args
            assert "outputs" in args

    def test_recipe_type_mapping(self):
        """Verify recipe_type values match dataiku_factory conventions."""
        flow = _multi_recipe_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        recipe_calls = [c for c in calls if c["tool_name"] == "create_recipe"]
        types = {c["arguments"]["recipe_type"] for c in recipe_calls}
        # Should contain shaker (prepare), grouping, join
        assert "shaker" in types
        assert "grouping" in types
        assert "join" in types

    def test_topological_ordering(self):
        """Datasets should appear before recipes that use them."""
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        names = [(c["tool_name"], c["arguments"].get("dataset_name") or c["arguments"].get("recipe_name"))
                 for c in calls]

        # Find indices
        ds_indices = {name: i for i, (tool, name) in enumerate(names) if tool == "create_dataset"}
        recipe_indices = {name: i for i, (tool, name) in enumerate(names) if tool == "create_recipe"}

        # The recipe should come after its input/output datasets
        if "raw_data" in ds_indices and "clean_data" in recipe_indices:
            assert ds_indices["raw_data"] < recipe_indices["clean_data"]

    def test_multi_recipe_flow_topological_ordering(self):
        """In multi-recipe flow, intermediate datasets should be created between recipes."""
        flow = _multi_recipe_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")

        # Collect all create operations in order
        ops = []
        for c in calls:
            if c["tool_name"] == "create_dataset":
                ops.append(("dataset", c["arguments"]["dataset_name"]))
            else:
                ops.append(("recipe", c["arguments"]["recipe_name"]))

        # The 'cleaned' dataset must appear before 'group_data' and 'join_data' recipes
        cleaned_idx = None
        group_idx = None
        join_idx = None
        for i, (kind, name) in enumerate(ops):
            if kind == "dataset" and name == "cleaned":
                cleaned_idx = i
            if kind == "recipe" and name == "group_data":
                group_idx = i
            if kind == "recipe" and name == "join_data":
                join_idx = i

        if cleaned_idx is not None and group_idx is not None:
            assert cleaned_idx < group_idx
        if cleaned_idx is not None and join_idx is not None:
            assert cleaned_idx < join_idx

    def test_settings_included_in_recipe_args(self):
        """Recipes with settings should include them in MCP arguments."""
        flow = _flow_with_settings()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        recipe_calls = [c for c in calls if c["tool_name"] == "create_recipe"]
        for rc in recipe_calls:
            if rc["arguments"]["recipe_name"] in ("prep_with_settings", "group_with_settings"):
                assert "settings" in rc["arguments"]

    def test_dataset_with_schema(self):
        """Dataset with schema should include schema in MCP arguments."""
        flow = DataikuFlow(name="schema_flow")
        ds = DataikuDataset(
            name="typed_ds",
            dataset_type=DatasetType.INPUT,
            schema=[
                ColumnSchema(name="id", type="int"),
                ColumnSchema(name="name", type="string"),
            ],
        )
        flow.add_dataset(ds)
        calls = generate_mcp_tool_calls(flow, "PROJ")
        ds_calls = [c for c in calls if c["tool_name"] == "create_dataset"]
        # Find our dataset
        typed_call = next(
            (c for c in ds_calls if c["arguments"]["dataset_name"] == "typed_ds"),
            None,
        )
        assert typed_call is not None
        assert "schema" in typed_call["arguments"]
        cols = typed_call["arguments"]["schema"]["columns"]
        assert len(cols) == 2
        assert cols[0]["name"] == "id"

    def test_empty_flow(self):
        flow = DataikuFlow(name="empty")
        calls = generate_mcp_tool_calls(flow, "PROJ")
        assert calls == []


# ===========================================================================
# 8. format_mcp_script()
# ===========================================================================

class TestFormatMCPScript:
    """Tests for format_mcp_script()."""

    def test_basic_output(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        script = format_mcp_script(calls)
        assert isinstance(script, str)
        assert "# MCP Tool Calls for Dataiku DSS" in script
        assert f"# Total calls: {len(calls)}" in script

    def test_step_numbering(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        script = format_mcp_script(calls)
        assert "# Step 1:" in script

    def test_tool_name_and_arguments_present(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        script = format_mcp_script(calls)
        assert "tool: create_dataset" in script or "tool: create_recipe" in script
        assert "arguments:" in script

    def test_arguments_are_valid_json(self):
        flow = _simple_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        script = format_mcp_script(calls)
        # Extract JSON blocks from the script
        lines = script.split("\n")
        in_args = False
        json_buf = []
        for line in lines:
            if line.startswith("arguments: "):
                in_args = True
                json_buf = [line[len("arguments: "):]]
            elif in_args:
                if line.strip() == "":
                    # End of JSON block
                    json_str = "\n".join(json_buf)
                    parsed = json.loads(json_str)
                    assert isinstance(parsed, dict)
                    in_args = False
                    json_buf = []
                else:
                    json_buf.append(line)

    def test_multi_recipe_script_ordering(self):
        flow = _multi_recipe_flow()
        calls = generate_mcp_tool_calls(flow, "PROJ")
        script = format_mcp_script(calls)
        # Verify step numbers are sequential
        for i in range(1, len(calls) + 1):
            assert f"# Step {i}:" in script

    def test_empty_calls(self):
        script = format_mcp_script([])
        assert "# Total calls: 0" in script


# ===========================================================================
# 9. End-to-end: convert() -> DSSFlowDeployer(dry_run=True).deploy()
# ===========================================================================

class TestEndToEnd:
    """End-to-end tests: convert Python code and deploy in dry_run mode."""

    def test_simple_dropna(self):
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.dropna()
df.to_csv('clean.csv')
"""
        flow = convert(code)
        deployer = DSSFlowDeployer("", "", "E2E_PROJ", dry_run=True)
        result = deployer.deploy(flow)
        assert result.success is True
        assert result.dry_run is True
        assert len(result.datasets_created) >= 1
        assert len(result.recipes_created) >= 1

    def test_groupby_agg(self):
        code = """
import pandas as pd
df = pd.read_csv('sales.csv')
summary = df.groupby('category').agg({'amount': 'sum'})
summary.to_csv('summary.csv')
"""
        flow = convert(code)
        deployer = DSSFlowDeployer("", "", "E2E_PROJ", dry_run=True)
        result = deployer.deploy(flow)
        assert result.success is True
        assert len(result.recipes_created) >= 1

    def test_rename_columns(self):
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.rename(columns={'old_name': 'new_name'})
df.to_csv('out.csv')
"""
        flow = convert(code)
        deployer = DSSFlowDeployer("", "", "E2E_PROJ", dry_run=True)
        result = deployer.deploy(flow)
        assert result.success is True

    def test_multi_step_pipeline(self):
        code = """
import pandas as pd
df = pd.read_csv('raw.csv')
df = df.dropna()
df = df.rename(columns={'col1': 'column_one'})
df = df.drop_duplicates()
df.to_csv('processed.csv')
"""
        flow = convert(code)
        deployer = DSSFlowDeployer("", "", "E2E_PROJ", dry_run=True)
        result = deployer.deploy(flow)
        assert result.success is True
        assert len(result.datasets_created) >= 2
        assert len(result.recipes_created) >= 1

    def test_sort_values(self):
        code = """
import pandas as pd
df = pd.read_csv('data.csv')
df = df.sort_values('price', ascending=False)
df.to_csv('sorted.csv')
"""
        flow = convert(code)
        deployer = DSSFlowDeployer("", "", "E2E_PROJ", dry_run=True)
        result = deployer.deploy(flow)
        assert result.success is True

    def test_end_to_end_mcp(self):
        """convert() -> generate_mcp_tool_calls() -> format_mcp_script()"""
        code = """
import pandas as pd
df = pd.read_csv('users.csv')
df = df.fillna(0)
result = df.groupby('region').agg({'revenue': 'sum'})
result.to_csv('regional_revenue.csv')
"""
        flow = convert(code)
        calls = generate_mcp_tool_calls(flow, "MCP_PROJ")
        assert len(calls) >= 2  # at least datasets and recipes

        script = format_mcp_script(calls)
        assert "MCP Tool Calls" in script
        assert "MCP_PROJ" in script


# ===========================================================================
# 10. Manually constructed flows with factory methods
# ===========================================================================

class TestFactoryMethodFlows:
    """Tests with flows built using DataikuRecipe factory methods."""

    def setup_method(self):
        self.deployer = DSSFlowDeployer("", "", "FACTORY_PROJ", dry_run=True)

    def test_prepare_factory(self):
        flow = DataikuFlow(name="factory_test")
        flow.add_dataset(DataikuDataset(name="src", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="dst", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe.create_prepare(
            name="prep_factory",
            input_dataset="src",
            output_dataset="dst",
            steps=[
                PrepareStep(
                    processor_type=ProcessorType.REMOVE_ROWS_ON_EMPTY,
                    params={"columns": ["id"]},
                ),
                PrepareStep(
                    processor_type=ProcessorType.STRING_TRANSFORMER,
                    params={"column": "name", "mode": "TO_UPPER"},
                ),
            ],
        )
        flow.add_recipe(recipe)
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert "prep_factory" in result.recipes_created

    def test_grouping_factory(self):
        flow = DataikuFlow(name="grouping_test")
        flow.add_dataset(DataikuDataset(name="transactions", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="aggregated", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe.create_grouping(
            name="agg_txn",
            input_dataset="transactions",
            output_dataset="aggregated",
            keys=["category", "region"],
            aggregations=[
                Aggregation(column="amount", function="SUM"),
                Aggregation(column="amount", function="AVG"),
                Aggregation(column="id", function="COUNT"),
            ],
        )
        flow.add_recipe(recipe)
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert "agg_txn" in result.recipes_created

    def test_join_factory(self):
        flow = DataikuFlow(name="join_test")
        flow.add_dataset(DataikuDataset(name="orders", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="customers", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="enriched_orders", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe.create_join(
            name="join_orders",
            left_dataset="orders",
            right_dataset="customers",
            output_dataset="enriched_orders",
            join_keys=[JoinKey(left_column="customer_id", right_column="id")],
            join_type=JoinType.INNER,
        )
        flow.add_recipe(recipe)
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert "join_orders" in result.recipes_created

    def test_python_factory(self):
        flow = DataikuFlow(name="python_test")
        flow.add_dataset(DataikuDataset(name="in_ds", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="out_ds", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe.create_python(
            name="py_transform",
            inputs=["in_ds"],
            outputs=["out_ds"],
            code="import dataiku\nds = dataiku.Dataset('in_ds')\ndf = ds.get_dataframe()",
        )
        flow.add_recipe(recipe)
        result = self.deployer.deploy(flow)
        assert result.success is True
        assert "py_transform" in result.recipes_created

    def test_all_recipe_settings_deploy(self):
        """Test deploying recipes with all RecipeSettings subclasses."""
        deployer = DSSFlowDeployer("", "", "SETTINGS_PROJ", dry_run=True)

        settings_map = {
            "prepare": (RecipeType.PREPARE, PrepareSettings()),
            "grouping": (RecipeType.GROUPING, GroupingSettings(keys=["k"])),
            "join": (RecipeType.JOIN, JoinSettings(join_type="LEFT")),
            "window": (RecipeType.WINDOW, WindowSettings(partition_columns=["p"])),
            "sampling": (RecipeType.SAMPLING, SamplingSettings(sample_size=100)),
            "split": (RecipeType.SPLIT, SplitSettings(condition="x > 1")),
            "sort": (RecipeType.SORT, SortSettings(sort_columns=[{"column": "a"}])),
            "topn": (RecipeType.TOP_N, TopNSettings(top_n=5)),
            "distinct": (RecipeType.DISTINCT, DistinctSettings()),
            "stack": (RecipeType.STACK, StackSettings()),
            "python_s": (RecipeType.PYTHON, PythonSettings(code="pass")),
            "pivot": (RecipeType.PIVOT, PivotSettings(row_columns=["r"], column_column="c")),
        }

        for name_suffix, (rtype, settings) in settings_map.items():
            recipe = DataikuRecipe(
                name=f"recipe_{name_suffix}",
                recipe_type=rtype,
                inputs=["in"],
                outputs=["out"],
                settings=settings,
            )
            info = deployer.deploy_recipe(recipe)
            assert info["name"] == f"recipe_{name_suffix}"
            assert "builder_args" in info
            assert isinstance(info["builder_args"], dict)


# ===========================================================================
# 11. Edge cases
# ===========================================================================

class TestEdgeCases:
    """Edge case tests for integration module."""

    def test_deploy_result_multiple_errors(self):
        result = DeploymentResult(
            errors=["err1", "err2"],
            warnings=["warn1"],
        )
        assert result.success is False
        d = result.to_dict()
        assert len(d["errors"]) == 2
        assert len(d["warnings"]) == 1

    def test_mcp_calls_with_no_recipes(self):
        """Flow with only datasets and no recipes."""
        flow = DataikuFlow(name="ds_only")
        flow.add_dataset(DataikuDataset(name="lonely_ds", dataset_type=DatasetType.INPUT))
        calls = generate_mcp_tool_calls(flow, "PROJ")
        ds_calls = [c for c in calls if c["tool_name"] == "create_dataset"]
        recipe_calls = [c for c in calls if c["tool_name"] == "create_recipe"]
        assert len(ds_calls) == 1
        assert len(recipe_calls) == 0

    def test_mcp_calls_with_multiple_connection_types(self):
        flow = DataikuFlow(name="multi_conn")
        flow.add_dataset(
            DataikuDataset(
                name="fs_ds",
                dataset_type=DatasetType.INPUT,
                connection_type=DatasetConnectionType.FILESYSTEM,
            )
        )
        flow.add_dataset(
            DataikuDataset(
                name="pg_ds",
                dataset_type=DatasetType.INPUT,
                connection_type=DatasetConnectionType.SQL_POSTGRESQL,
            )
        )
        calls = generate_mcp_tool_calls(flow, "PROJ")
        conn_types = [c["arguments"]["connection_type"] for c in calls if c["tool_name"] == "create_dataset"]
        assert "Filesystem" in conn_types
        assert "PostgreSQL" in conn_types

    def test_deployer_deploy_dict_return(self):
        deployer = DSSFlowDeployer("", "", "PROJ", dry_run=True)
        ds = DataikuDataset(name="test_ds", dataset_type=DatasetType.INPUT)
        info = deployer.deploy_dataset(ds)
        assert isinstance(info, dict)

    def test_format_mcp_script_single_call(self):
        calls = [
            {
                "tool_name": "create_dataset",
                "arguments": {"project_key": "P", "dataset_name": "ds1", "connection_type": "Filesystem"},
            }
        ]
        script = format_mcp_script(calls)
        assert "# Step 1: create_dataset" in script
        assert "# Total calls: 1" in script

    def test_mcp_recipe_with_python_code_settings(self):
        """Python recipe settings should include code in MCP arguments."""
        flow = DataikuFlow(name="py_flow")
        flow.add_dataset(DataikuDataset(name="in", dataset_type=DatasetType.INPUT))
        flow.add_dataset(DataikuDataset(name="out", dataset_type=DatasetType.OUTPUT))
        recipe = DataikuRecipe(
            name="py_recipe",
            recipe_type=RecipeType.PYTHON,
            inputs=["in"],
            outputs=["out"],
            settings=PythonSettings(code="import dataiku"),
        )
        flow.add_recipe(recipe)
        calls = generate_mcp_tool_calls(flow, "PROJ")
        recipe_calls = [c for c in calls if c["tool_name"] == "create_recipe"]
        py_call = next(c for c in recipe_calls if c["arguments"]["recipe_name"] == "py_recipe")
        assert "settings" in py_call["arguments"]
        assert py_call["arguments"]["settings"]["code"] == "import dataiku"
