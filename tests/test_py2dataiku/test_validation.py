"""Tests for py2dataiku validation utilities."""

import pytest

from py2dataiku.utils.validation import (
    validate_recipe_config,
    validate_flow,
    _validate_prepare_settings,
    _validate_prepare_step,
    _validate_join_settings,
    _validate_grouping_settings,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _valid_recipe(**overrides):
    base = {
        "type": "sync",
        "name": "recipe_1",
        "inputs": [{"ref": "ds_in"}],
        "outputs": [{"ref": "ds_out"}],
    }
    base.update(overrides)
    return base


def _valid_flow(**overrides):
    base = {
        "datasets": [{"name": "ds_in"}, {"name": "ds_out"}],
        "recipes": [_valid_recipe()],
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# validate_recipe_config – required fields
# ---------------------------------------------------------------------------

class TestValidateRecipeConfigRequiredFields:
    """Ensure required top-level fields are checked."""

    def test_valid_minimal_recipe_passes(self):
        is_valid, errors = validate_recipe_config(_valid_recipe())
        assert is_valid is True
        assert errors == []

    def test_missing_type_is_error(self):
        recipe = _valid_recipe()
        del recipe["type"]
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("type" in e for e in errors)

    def test_missing_name_is_error(self):
        recipe = _valid_recipe()
        del recipe["name"]
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("name" in e for e in errors)

    def test_missing_inputs_is_error(self):
        recipe = _valid_recipe()
        del recipe["inputs"]
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("inputs" in e for e in errors)

    def test_missing_outputs_is_error(self):
        recipe = _valid_recipe()
        del recipe["outputs"]
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("outputs" in e for e in errors)

    def test_all_required_fields_missing_returns_multiple_errors(self):
        is_valid, errors = validate_recipe_config({})
        assert is_valid is False
        assert len(errors) >= 4


# ---------------------------------------------------------------------------
# validate_recipe_config – inputs / outputs format
# ---------------------------------------------------------------------------

class TestValidateRecipeConfigInputsOutputs:
    """inputs and outputs must be lists of dicts with 'ref'."""

    def test_inputs_not_list_is_error(self):
        recipe = _valid_recipe(inputs="not_a_list")
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("inputs" in e for e in errors)

    def test_outputs_not_list_is_error(self):
        recipe = _valid_recipe(outputs="not_a_list")
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("outputs" in e for e in errors)

    def test_input_missing_ref_is_error(self):
        recipe = _valid_recipe(inputs=[{"name": "ds_in"}])
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("Input 0" in e for e in errors)

    def test_output_missing_ref_is_error(self):
        recipe = _valid_recipe(outputs=[{"name": "ds_out"}])
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False
        assert any("Output 0" in e for e in errors)

    def test_multiple_valid_inputs_and_outputs(self):
        recipe = _valid_recipe(
            inputs=[{"ref": "a"}, {"ref": "b"}],
            outputs=[{"ref": "c"}, {"ref": "d"}],
        )
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is True

    def test_input_is_not_dict_is_error(self):
        recipe = _valid_recipe(inputs=["just_a_string"])
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False


# ---------------------------------------------------------------------------
# validate_recipe_config – prepare type
# ---------------------------------------------------------------------------

class TestValidateRecipeConfigPrepare:
    """Type-specific validation for 'prepare' recipes."""

    def _prepare_recipe(self, steps=None):
        return _valid_recipe(
            type="prepare",
            settings={"steps": steps if steps is not None else []},
        )

    def test_prepare_with_no_steps_is_valid(self):
        is_valid, errors = validate_recipe_config(self._prepare_recipe())
        assert is_valid is True

    def test_prepare_with_valid_fill_empty_step(self):
        step = {
            "type": "FillEmptyWithValue",
            "params": {"column": "age", "value": "0"},
        }
        is_valid, errors = validate_recipe_config(self._prepare_recipe([step]))
        assert is_valid is True, errors

    def test_prepare_step_missing_type_is_error(self):
        step = {"params": {"column": "x"}}
        is_valid, errors = validate_recipe_config(self._prepare_recipe([step]))
        assert is_valid is False
        assert any("Step 0" in e for e in errors)

    def test_prepare_step_unknown_type_is_error(self):
        step = {"type": "NonExistentProcessor", "params": {}}
        is_valid, errors = validate_recipe_config(self._prepare_recipe([step]))
        assert is_valid is False

    def test_prepare_step_missing_required_param_is_error(self):
        # FillEmptyWithValue requires 'column' and 'value'
        step = {"type": "FillEmptyWithValue", "params": {"column": "age"}}
        is_valid, errors = validate_recipe_config(self._prepare_recipe([step]))
        assert is_valid is False
        assert any("value" in e for e in errors)

    def test_prepare_steps_not_list_is_error(self):
        recipe = _valid_recipe(type="prepare", settings={"steps": "bad"})
        is_valid, errors = validate_recipe_config(recipe)
        assert is_valid is False

    def test_prepare_with_valid_column_renamer(self):
        step = {
            "type": "ColumnRenamer",
            "params": {"renamings": [{"from": "a", "to": "b"}]},
        }
        is_valid, errors = validate_recipe_config(self._prepare_recipe([step]))
        assert is_valid is True, errors

    def test_prepare_with_column_renamer_missing_required(self):
        step = {"type": "ColumnRenamer", "params": {}}
        is_valid, errors = validate_recipe_config(self._prepare_recipe([step]))
        assert is_valid is False


# ---------------------------------------------------------------------------
# validate_recipe_config – join type
# ---------------------------------------------------------------------------

class TestValidateRecipeConfigJoin:
    """Type-specific validation for 'join' recipes."""

    def _join_recipe(self, settings=None):
        return _valid_recipe(
            type="join",
            inputs=[{"ref": "left"}, {"ref": "right"}],
            settings=settings or {},
        )

    def test_join_without_conditions_is_error(self):
        is_valid, errors = validate_recipe_config(self._join_recipe())
        assert is_valid is False
        assert any("join condition" in e.lower() for e in errors)

    def test_join_with_valid_condition(self):
        settings = {
            "joinType": "INNER",
            "joins": [{"left": {"column": "id"}, "right": {"column": "id"}}],
        }
        is_valid, errors = validate_recipe_config(self._join_recipe(settings))
        assert is_valid is True, errors

    def test_join_invalid_join_type_is_error(self):
        settings = {
            "joinType": "CARTESIAN",
            "joins": [{"left": {"column": "id"}, "right": {"column": "id"}}],
        }
        is_valid, errors = validate_recipe_config(self._join_recipe(settings))
        assert is_valid is False
        assert any("join type" in e.lower() for e in errors)

    def test_join_condition_missing_left_is_error(self):
        settings = {
            "joins": [{"right": {"column": "id"}}],
        }
        is_valid, errors = validate_recipe_config(self._join_recipe(settings))
        assert is_valid is False

    def test_join_condition_missing_right_is_error(self):
        settings = {
            "joins": [{"left": {"column": "id"}}],
        }
        is_valid, errors = validate_recipe_config(self._join_recipe(settings))
        assert is_valid is False

    def test_join_condition_left_missing_column_is_error(self):
        settings = {
            "joins": [{"left": {}, "right": {"column": "id"}}],
        }
        is_valid, errors = validate_recipe_config(self._join_recipe(settings))
        assert is_valid is False
        assert any("left" in e and "column" in e for e in errors)

    def test_join_condition_right_missing_column_is_error(self):
        settings = {
            "joins": [{"left": {"column": "id"}, "right": {}}],
        }
        is_valid, errors = validate_recipe_config(self._join_recipe(settings))
        assert is_valid is False

    def test_all_valid_join_types(self):
        for jt in ["INNER", "LEFT", "RIGHT", "OUTER", "CROSS"]:
            settings = {
                "joinType": jt,
                "joins": [{"left": {"column": "id"}, "right": {"column": "id"}}],
            }
            is_valid, errors = validate_recipe_config(self._join_recipe(settings))
            assert is_valid is True, f"{jt}: {errors}"


# ---------------------------------------------------------------------------
# validate_recipe_config – grouping type
# ---------------------------------------------------------------------------

class TestValidateRecipeConfigGrouping:
    """Type-specific validation for 'grouping' recipes."""

    def _grouping_recipe(self, settings=None):
        return _valid_recipe(type="grouping", settings=settings or {})

    def test_grouping_without_keys_is_error(self):
        is_valid, errors = validate_recipe_config(self._grouping_recipe())
        assert is_valid is False
        assert any("key" in e.lower() for e in errors)

    def test_grouping_with_valid_settings(self):
        settings = {
            "keys": ["category"],
            "aggregations": [{"column": "amount", "type": "SUM"}],
        }
        is_valid, errors = validate_recipe_config(self._grouping_recipe(settings))
        assert is_valid is True, errors

    def test_grouping_aggregation_missing_column_is_error(self):
        settings = {
            "keys": ["category"],
            "aggregations": [{"type": "SUM"}],
        }
        is_valid, errors = validate_recipe_config(self._grouping_recipe(settings))
        assert is_valid is False
        assert any("column" in e for e in errors)

    def test_grouping_aggregation_missing_type_is_error(self):
        settings = {
            "keys": ["category"],
            "aggregations": [{"column": "amount"}],
        }
        is_valid, errors = validate_recipe_config(self._grouping_recipe(settings))
        assert is_valid is False
        assert any("type" in e for e in errors)

    def test_grouping_aggregation_invalid_type_is_error(self):
        settings = {
            "keys": ["category"],
            "aggregations": [{"column": "amount", "type": "INVALID"}],
        }
        is_valid, errors = validate_recipe_config(self._grouping_recipe(settings))
        assert is_valid is False

    def test_grouping_all_valid_agg_types(self):
        valid_types = [
            "SUM", "AVG", "COUNT", "MIN", "MAX",
            "FIRST", "LAST", "STDDEV", "VAR", "MEDIAN",
            "COUNTDISTINCT", "LIST", "CONCAT",
        ]
        for agg_type in valid_types:
            settings = {
                "keys": ["cat"],
                "aggregations": [{"column": "val", "type": agg_type}],
            }
            is_valid, errors = validate_recipe_config(self._grouping_recipe(settings))
            assert is_valid is True, f"{agg_type}: {errors}"


# ---------------------------------------------------------------------------
# validate_flow
# ---------------------------------------------------------------------------

class TestValidateFlow:
    """Tests for validate_flow()."""

    def test_valid_flow_passes(self):
        is_valid, errors = validate_flow(_valid_flow())
        assert is_valid is True
        assert errors == []

    def test_flow_missing_datasets_is_error(self):
        flow = _valid_flow()
        del flow["datasets"]
        is_valid, errors = validate_flow(flow)
        assert is_valid is False
        assert any("datasets" in e for e in errors)

    def test_flow_missing_recipes_is_error(self):
        flow = _valid_flow()
        del flow["recipes"]
        is_valid, errors = validate_flow(flow)
        assert is_valid is False
        assert any("recipes" in e for e in errors)

    def test_flow_recipe_input_not_in_datasets_is_error(self):
        flow = {
            "datasets": [{"name": "ds_out"}],
            "recipes": [_valid_recipe(inputs=[{"ref": "missing_ds"}])],
        }
        is_valid, errors = validate_flow(flow)
        assert is_valid is False
        assert any("missing_ds" in e for e in errors)

    def test_flow_recipe_output_not_in_datasets_is_error(self):
        flow = {
            "datasets": [{"name": "ds_in"}],
            "recipes": [_valid_recipe(outputs=[{"ref": "missing_out"}])],
        }
        is_valid, errors = validate_flow(flow)
        assert is_valid is False
        assert any("missing_out" in e for e in errors)

    def test_flow_with_multiple_valid_recipes(self):
        flow = {
            "datasets": [
                {"name": "raw"},
                {"name": "clean"},
                {"name": "agg"},
            ],
            "recipes": [
                _valid_recipe(name="r1", inputs=[{"ref": "raw"}], outputs=[{"ref": "clean"}]),
                _valid_recipe(name="r2", inputs=[{"ref": "clean"}], outputs=[{"ref": "agg"}]),
            ],
        }
        is_valid, errors = validate_flow(flow)
        assert is_valid is True, errors

    def test_flow_empty_recipes_and_datasets_is_valid(self):
        flow = {"datasets": [], "recipes": []}
        is_valid, errors = validate_flow(flow)
        assert is_valid is True

    def test_flow_propagates_recipe_errors(self):
        # A recipe with a missing 'type' field
        bad_recipe = {"name": "r", "inputs": [{"ref": "ds_in"}], "outputs": [{"ref": "ds_out"}]}
        flow = {
            "datasets": [{"name": "ds_in"}, {"name": "ds_out"}],
            "recipes": [bad_recipe],
        }
        is_valid, errors = validate_flow(flow)
        assert is_valid is False
