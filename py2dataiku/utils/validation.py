"""Validation utilities for Dataiku configurations."""

from typing import Any, Dict, List, Optional, Tuple

from py2dataiku.mappings.processor_catalog import ProcessorCatalog


def validate_recipe_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a Dataiku recipe configuration.

    Args:
        config: Recipe configuration dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check required fields
    if "type" not in config:
        errors.append("Missing required field: 'type'")
    if "name" not in config:
        errors.append("Missing required field: 'name'")
    if "inputs" not in config:
        errors.append("Missing required field: 'inputs'")
    if "outputs" not in config:
        errors.append("Missing required field: 'outputs'")

    # Validate inputs format
    inputs = config.get("inputs", [])
    if not isinstance(inputs, list):
        errors.append("'inputs' must be a list")
    else:
        for i, inp in enumerate(inputs):
            if not isinstance(inp, dict) or "ref" not in inp:
                errors.append(f"Input {i} must be a dict with 'ref' key")

    # Validate outputs format
    outputs = config.get("outputs", [])
    if not isinstance(outputs, list):
        errors.append("'outputs' must be a list")
    else:
        for i, out in enumerate(outputs):
            if not isinstance(out, dict) or "ref" not in out:
                errors.append(f"Output {i} must be a dict with 'ref' key")

    # Type-specific validation
    recipe_type = config.get("type")
    settings = config.get("settings", {})

    if recipe_type == "prepare":
        errors.extend(_validate_prepare_settings(settings))
    elif recipe_type == "join":
        errors.extend(_validate_join_settings(settings))
    elif recipe_type == "grouping":
        errors.extend(_validate_grouping_settings(settings))

    return len(errors) == 0, errors


def _validate_prepare_settings(settings: Dict[str, Any]) -> List[str]:
    """Validate Prepare recipe settings."""
    errors = []

    steps = settings.get("steps", [])
    if not isinstance(steps, list):
        errors.append("Prepare 'steps' must be a list")
        return errors

    for i, step in enumerate(steps):
        step_errors = _validate_prepare_step(step, i)
        errors.extend(step_errors)

    return errors


def _validate_prepare_step(step: Dict[str, Any], index: int) -> List[str]:
    """Validate a single Prepare step."""
    errors = []

    if "type" not in step:
        errors.append(f"Step {index}: missing 'type' field")
        return errors

    step_type = step["type"]
    processor_info = ProcessorCatalog.get_processor(step_type)

    if not processor_info:
        errors.append(f"Step {index}: unknown processor type '{step_type}'")
        return errors

    # Check required parameters
    params = step.get("params", {})
    for required_param in processor_info.required_params:
        if required_param not in params:
            errors.append(
                f"Step {index} ({step_type}): missing required parameter '{required_param}'"
            )

    return errors


def _validate_join_settings(settings: Dict[str, Any]) -> List[str]:
    """Validate Join recipe settings."""
    errors = []

    # Check join type
    join_type = settings.get("joinType")
    valid_types = {"INNER", "LEFT", "RIGHT", "OUTER", "CROSS"}
    if join_type and join_type not in valid_types:
        errors.append(f"Invalid join type: '{join_type}'")

    # Check joins (join conditions)
    joins = settings.get("joins", [])
    if not joins:
        errors.append("Join recipe must have at least one join condition")
    else:
        for i, join in enumerate(joins):
            if "left" not in join or "right" not in join:
                errors.append(f"Join condition {i}: missing 'left' or 'right'")
            else:
                if "column" not in join.get("left", {}):
                    errors.append(f"Join condition {i}: left side missing 'column'")
                if "column" not in join.get("right", {}):
                    errors.append(f"Join condition {i}: right side missing 'column'")

    return errors


def _validate_grouping_settings(settings: Dict[str, Any]) -> List[str]:
    """Validate Grouping recipe settings."""
    errors = []

    # Check keys
    keys = settings.get("keys", [])
    if not keys:
        errors.append("Grouping recipe should have at least one key")

    # Check aggregations
    aggregations = settings.get("aggregations", [])
    valid_agg_types = {
        "SUM", "AVG", "COUNT", "MIN", "MAX",
        "FIRST", "LAST", "STDDEV", "VAR", "MEDIAN",
        "COUNTDISTINCT", "LIST", "CONCAT",
    }

    for i, agg in enumerate(aggregations):
        if "column" not in agg:
            errors.append(f"Aggregation {i}: missing 'column'")
        if "type" not in agg:
            errors.append(f"Aggregation {i}: missing 'type'")
        elif agg["type"] not in valid_agg_types:
            errors.append(f"Aggregation {i}: invalid type '{agg['type']}'")

    return errors


def validate_flow(flow_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a complete Dataiku flow configuration.

    Args:
        flow_config: Flow configuration dictionary

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []

    # Check required fields
    if "datasets" not in flow_config:
        errors.append("Missing 'datasets' in flow configuration")
    if "recipes" not in flow_config:
        errors.append("Missing 'recipes' in flow configuration")

    # Validate each recipe
    for recipe in flow_config.get("recipes", []):
        is_valid, recipe_errors = validate_recipe_config(recipe)
        errors.extend(recipe_errors)

    # Check dataset references
    datasets = {ds["name"] for ds in flow_config.get("datasets", [])}
    for recipe in flow_config.get("recipes", []):
        for inp in recipe.get("inputs", []):
            ref = inp.get("ref")
            if ref and ref not in datasets:
                errors.append(f"Recipe '{recipe.get('name')}': input '{ref}' not found in datasets")
        for out in recipe.get("outputs", []):
            ref = out.get("ref")
            if ref and ref not in datasets:
                errors.append(f"Recipe '{recipe.get('name')}': output '{ref}' not found in datasets")

    return len(errors) == 0, errors
