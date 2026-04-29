"""Conversion service — thin wrapper over py2dataiku.api.convert / convert_with_llm."""

from __future__ import annotations

import ast
import logging
from typing import Any

from py2dataiku import convert, convert_with_llm
from py2dataiku.exceptions import ConfigurationError, Py2DataikuError

from ..errors import problem_dict
from ..schemas.convert import ConvertMode, ConvertRequest, ConvertResponse
from ..schemas.flow import DataikuFlowModel
from .llm_credentials import resolve_api_key
from .score import score_flow
from .streaming import ConversionEventEmitter

logger = logging.getLogger(__name__)


_OUTPUT_SINK_HINTS: tuple[str, ...] = (
    "_pivoted",
    "_grouped",
    "_topn",
    "_split_",
)


def _sanitize_flow_dict(flow_dict: dict[str, Any]) -> list[str]:
    """Scrub the rule-based-generator flow dict before serializing to the wire.

    Three problems this addresses, all visible in textbook examples 02/04:

    1. **Empty-string dataset placeholder**: chained ``groupby(...).rolling(...)
       .reset_index().rename(...)`` lineage runs out of variable-name tracking
       and registers an empty-name dataset (``""``) plus a ``recipe.inputs=[""]``.
       That breaks ReactFlow / FlowCanvas (an edge with id ``""`` collides with
       the empty default key) and confuses the Inspector.  We drop the empty
       placeholder dataset and re-route the empty input to the most recent
       recipe's first output when one exists; otherwise we just drop the input.

    2. **Bracket-notation dataset names**: ``events['events_in_session']`` and
       similar names that leak from subscript-target assignments. They are
       valid identifiers in DSS JSON but render as garbled labels in the UI.
       We rewrite them to a sanitized form (``events_events_in_session``) so
       they show up cleanly as recipe-output stripes.

    3. **Output-dataset under-counting** for terminal datasets: a dataset with
       no downstream consumer that originated from a recipe output gets bumped
       from ``intermediate`` → ``output`` so ``score.dataset_count`` and the
       UI's "Datasets" stat reflect what a reader would expect.

    Returns the list of sanitization warnings to append to ``flow.warnings``.
    """
    warnings: list[str] = []
    datasets: list[dict[str, Any]] = list(flow_dict.get("datasets") or [])
    recipes: list[dict[str, Any]] = list(flow_dict.get("recipes") or [])

    # ---- 1. empty-string dataset reference scrub ----
    has_empty_ds = any((ds.get("name") == "") for ds in datasets)
    if has_empty_ds:
        warnings.append(
            "Removed empty-name dataset placeholder; the upstream recipe lost "
            "lineage tracking through a chained groupby/rolling/reset_index pattern."
        )
    datasets = [ds for ds in datasets if ds.get("name", "") != ""]

    # Track previous recipe output to re-route empty inputs.
    prev_outputs: list[str] = []
    for recipe in recipes:
        inputs = list(recipe.get("inputs") or [])
        outputs = list(recipe.get("outputs") or [])
        new_inputs: list[str] = []
        for ref in inputs:
            if ref == "":
                # Re-route to upstream recipe's first non-empty output, if any.
                upstream = next((o for o in prev_outputs if o), None)
                if upstream:
                    new_inputs.append(upstream)
                # otherwise drop the empty input — Pydantic won't accept "".
            else:
                new_inputs.append(ref)
        recipe["inputs"] = new_inputs
        prev_outputs = [o for o in outputs if o]

    # ---- 2. bracket-notation dataset name normalization ----
    name_rewrites: dict[str, str] = {}
    for ds in datasets:
        old = ds.get("name", "")
        if "[" in old and "]" in old:
            new = (
                old.replace("['", "_")
                .replace("']", "")
                .replace('["', "_")
                .replace('"]', "")
                .replace("[", "_")
                .replace("]", "")
            )
            # Avoid collisions with an existing name.
            base = new
            suffix = 1
            existing = {d.get("name", "") for d in datasets if d is not ds}
            while new in existing:
                suffix += 1
                new = f"{base}_{suffix}"
            if new != old:
                name_rewrites[old] = new
                ds["name"] = new
    if name_rewrites:
        for recipe in recipes:
            recipe["inputs"] = [name_rewrites.get(x, x) for x in (recipe.get("inputs") or [])]
            recipe["outputs"] = [name_rewrites.get(x, x) for x in (recipe.get("outputs") or [])]
        warnings.append(
            "Normalized "
            + ", ".join(f"'{k}' -> '{v}'" for k, v in name_rewrites.items())
            + " (subscript-target dataset names)."
        )

    # ---- 3. output-dataset role promotion ----
    # Any dataset that is referenced as an output but never as a downstream
    # input is a terminal dataset; promote it from intermediate to output so
    # the UI's "Datasets" badge is accurate.
    consumed: set[str] = set()
    produced: set[str] = set()
    for recipe in recipes:
        for ref in recipe.get("inputs") or []:
            consumed.add(ref)
        for ref in recipe.get("outputs") or []:
            produced.add(ref)
    promoted: list[str] = []
    for ds in datasets:
        nm = ds.get("name", "")
        if not nm:
            continue
        is_terminal = nm in produced and nm not in consumed
        if is_terminal and ds.get("type") == "intermediate":
            ds["type"] = "output"
            promoted.append(nm)
    if promoted:
        warnings.append(
            "Promoted terminal datasets to output: " + ", ".join(promoted)
        )

    # ---- 4. orphan-output sink merge ----
    # When a script ends with `df.to_csv("foo.csv")`, the LLM analyzer
    # frequently emits a separate output dataset (`foo_csv`) marked
    # is_output=True but doesn't tie it to any recipe — the recipe whose
    # output is `df` is the actual producer. The result is two datasets
    # for the same logical sink. We detect orphan output datasets whose
    # `source_variable` matches a producing recipe's output (after
    # stripping common file extensions) and either (a) promote the
    # producing dataset to terminal-output and drop the orphan, or
    # (b) attach the orphan to the producing recipe's outputs list.
    # Approach (b) preserves the user's explicit sink path; we use it
    # when the orphan's name differs materially from the upstream name.
    def _basename(s: str) -> str:
        """Strip directory + common file extensions for sink-name matching."""
        s = s.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        for ext in (".csv", ".parquet", ".json", ".tsv", ".feather", ".pickle", ".pkl"):
            if s.lower().endswith(ext):
                s = s[: -len(ext)]
                break
        return s.replace(" ", "_")

    output_role: dict[str, dict[str, Any]] = {
        ds.get("name", ""): ds for ds in datasets if ds.get("type") == "output"
    }
    orphan_merges: list[str] = []
    for ds in list(datasets):
        nm = ds.get("name", "")
        if not nm or nm not in output_role:
            continue
        if nm in produced:
            continue  # not orphan — some recipe already produces it
        # Match the orphan's source_variable against existing recipe outputs.
        sink_path = ds.get("source_variable") or ""
        sink_basename = _basename(sink_path) if sink_path else _basename(nm)
        candidates = [r for r in recipes if any(
            o == sink_basename or _basename(o) == sink_basename
            for o in (r.get("outputs") or [])
        )]
        if not candidates:
            # Try a softer match: the upstream output that's a prefix of
            # the orphan name (e.g., `top_50` upstream → `top_50_netting_sets_csv`).
            candidates = [r for r in recipes if any(
                sink_basename.startswith(o) or o.startswith(sink_basename)
                for o in (r.get("outputs") or [])
            )]
        if not candidates:
            continue  # genuinely orphaned; leave as-is
        # Attach the orphan to the producing recipe's outputs list rather
        # than merging it into another dataset's name. This preserves the
        # user's explicit sink path as a distinct dataset stripe.
        producer = candidates[0]
        existing_outputs = list(producer.get("outputs") or [])
        if nm not in existing_outputs:
            existing_outputs.append(nm)
            producer["outputs"] = existing_outputs
        produced.add(nm)
        orphan_merges.append(f"'{nm}' attached to recipe '{producer.get('name')}'")
    if orphan_merges:
        warnings.append(
            "Attached orphan output datasets to producing recipes: "
            + "; ".join(orphan_merges)
        )

    # ---- 5. self-loop auto-rename ----
    # Both rule-based (idioms like df["x"] = df["x"].fillna(0) on a single
    # frame) and LLM (despite the system-prompt rule) occasionally produce
    # recipes whose input and output share a dataset name. The downstream
    # DataikuRecipeModel Pydantic validator rejects these as cycles.
    # Auto-rename the colliding output to <name>_step_N so the validator
    # passes while preserving the recipe's intent. Subsequent recipes
    # that fed off the original name need their inputs rewritten too.
    self_loop_rewrites: list[str] = []
    name_remap: dict[str, str] = {}
    for idx, recipe in enumerate(recipes):
        inputs_set = set(recipe.get("inputs") or [])
        outputs = list(recipe.get("outputs") or [])
        new_outputs: list[str] = []
        for out in outputs:
            # Apply any prior remap propagated through the chain.
            out = name_remap.get(out, out)
            if out in inputs_set:
                # Pick a fresh name; avoid collisions with existing dataset
                # names by suffixing _step_2, _step_3, ...
                base = out
                suffix = 2
                existing = {ds.get("name", "") for ds in datasets} | set(
                    new_outputs
                )
                while f"{base}_step_{suffix}" in existing:
                    suffix += 1
                fresh = f"{base}_step_{suffix}"
                name_remap[out] = fresh
                self_loop_rewrites.append(
                    f"recipe '{recipe.get('name')}': '{out}' -> '{fresh}'"
                )
                # Add a fresh dataset entry for the renamed output.
                # Copy the dataset model from the original where possible
                # so connection_type / type / schema flow through.
                template = next(
                    (ds for ds in datasets if ds.get("name") == base), None
                )
                new_ds = dict(template) if template else {"name": fresh}
                new_ds["name"] = fresh
                new_ds.setdefault("type", "intermediate")
                datasets.append(new_ds)
                new_outputs.append(fresh)
            else:
                new_outputs.append(out)
        recipe["outputs"] = new_outputs
        # Apply name_remap to any subsequent recipe's inputs that referenced
        # the original (now-renamed) name.
        for later in recipes[idx + 1 :]:
            later["inputs"] = [
                name_remap.get(x, x) for x in (later.get("inputs") or [])
            ]
    if self_loop_rewrites:
        warnings.append(
            "Renamed self-loop outputs to fresh names: "
            + "; ".join(self_loop_rewrites)
        )

    flow_dict["datasets"] = datasets
    flow_dict["recipes"] = recipes
    flow_dict["total_datasets"] = len(datasets)
    flow_dict["total_recipes"] = len(recipes)

    # Defensive: drop recipes that lost both their input and output via the
    # rewrites — a recipe with empty inputs and empty outputs is a dangling
    # node and would render as a free-floating circle.
    flow_dict["recipes"] = [
        r for r in flow_dict["recipes"]
        if (r.get("inputs") or []) or (r.get("outputs") or [])
    ]
    flow_dict["total_recipes"] = len(flow_dict["recipes"])
    return warnings


def convert_sync(req: ConvertRequest) -> ConvertResponse:
    """Convert Python code to a DataikuFlow and return a ConvertResponse.

    For rule mode: calls py2dataiku.convert().
    For llm mode: resolves provider/model/key from request options then env vars,
    raises ConfigurationError if no key is found, then calls convert_with_llm().

    Py2DataikuError subclasses propagate up to the global error handler in main.py.
    """
    optimize = req.options.optimize if req.options is not None else True

    if req.mode == ConvertMode.RULE:
        flow = convert(req.code, optimize=optimize)
    else:
        # LLM mode — resolve provider, model, api_key
        provider = (
            req.options.provider
            if req.options is not None and req.options.provider is not None
            else "anthropic"
        )
        model = (
            req.options.model
            if req.options is not None and req.options.model is not None
            else None
        )
        temperature = (
            req.options.temperature
            if req.options is not None and req.options.temperature is not None
            else 0.0
        )

        # Key resolution: persisted file (Settings → LLM Provider) wins,
        # env-var (ANTHROPIC_API_KEY / OPENAI_API_KEY) is the fallback. The
        # raw key is never logged.
        api_key, source = _resolve_api_key_for_request(provider)
        if not api_key:
            key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
            raise ConfigurationError(
                f"LLM mode requires an API key for provider '{provider}'. "
                f"Set it via Settings → LLM Provider in the UI, or export "
                f"{key_env} in the API server environment."
            )
        logger.debug(
            "Resolved LLM key", extra={"provider": provider, "source": source}
        )

        try:
            flow = convert_with_llm(
                req.code,
                provider=provider,
                api_key=api_key,
                model=model,
                optimize=optimize,
                temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001
            # Anthropic and OpenAI raise SDK-specific exceptions for
            # quota / rate-limit / auth errors. We catch the broad set
            # and translate to a structured 4xx so the UI banner /
            # CLI consumers don't see an opaque 500.
            msg = str(exc)
            from fastapi import HTTPException

            low = msg.lower()
            if "usage limit" in low or "spend limit" in low or "quota" in low:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "type": "/errors/llm-quota-exceeded",
                        "title": "LLM provider usage limit reached",
                        "status": 402,
                        "detail": msg,
                        "suggestion": (
                            "Wait for the quota window to reset, raise the "
                            "spend cap on your provider account, or switch "
                            "to mode='rule' for offline conversion."
                        ),
                    },
                ) from exc
            if "rate limit" in low or "429" in low:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "type": "/errors/llm-rate-limited",
                        "title": "LLM provider rate limited",
                        "status": 429,
                        "detail": msg,
                    },
                ) from exc
            if "authentication" in low or "401" in low or "invalid api key" in low:
                raise HTTPException(
                    status_code=401,
                    detail={
                        "type": "/errors/llm-auth",
                        "title": "LLM provider authentication failed",
                        "status": 401,
                        "detail": msg,
                        "suggestion": (
                            "Re-enter the API key in Settings -> LLM "
                            "Provider, or verify the key in the provider "
                            "dashboard."
                        ),
                    },
                ) from exc
            raise

    flow_dict = flow.to_dict()
    extra_warnings = _sanitize_flow_dict(flow_dict)
    flow_model = DataikuFlowModel.model_validate(flow_dict)
    score = score_flow(flow)
    # Reconcile recipe_count / dataset_count with the sanitized flow so the
    # UI's "Datasets" / "Recipes" badges match what the user actually sees
    # on the canvas after empty-name datasets / dangling recipes are scrubbed.
    score_updates: dict = {
        "recipe_count": len(flow_dict.get("recipes") or []),
        "dataset_count": len(flow_dict.get("datasets") or []),
    }
    # Surface token usage + an estimated USD cost when the analyzer
    # exposed it (LLM mode only — None for rule-based and MockProvider
    # paths that didn't supply usage).
    llm_usage = getattr(flow, "llm_usage", None)
    if llm_usage:
        score_updates["usage"] = {
            "input_tokens": llm_usage.get("input_tokens"),
            "output_tokens": llm_usage.get("output_tokens"),
            "cache_read_input_tokens": llm_usage.get("cache_read_input_tokens"),
            "cache_creation_input_tokens": llm_usage.get(
                "cache_creation_input_tokens"
            ),
        }
        # Anthropic Sonnet 4 list pricing (April 2026): input $3/MTok,
        # cached $0.30/MTok, output $15/MTok. Approximate; the real
        # dashboard is the source of truth for billing.
        in_tok = llm_usage.get("input_tokens") or 0
        out_tok = llm_usage.get("output_tokens") or 0
        cached = llm_usage.get("cache_read_input_tokens") or 0
        score_updates["cost_estimate"] = round(
            (in_tok * 3.0 + cached * 0.30 + out_tok * 15.0) / 1_000_000, 6
        )
    score = score.model_copy(update=score_updates)

    return ConvertResponse(
        flow=flow_model,
        score=score,
        warnings=list(flow.warnings) + extra_warnings,
    )


def _resolve_api_key_for_request(provider: str) -> tuple[str | None, str]:
    """Resolve the API key for *provider* via the file → env-var ladder.

    Pulls ``Settings.flows_dir`` lazily so tests rebinding the cached
    settings (apps/api/tests/conftest.py) reach the right tmp dir at request
    time.
    """
    # Local import to avoid a circular import at module load (deps imports
    # cost_meter which imports llm_audit but never conversion). Keeping this
    # import inline also lets tests override ``get_settings`` without the
    # service module having captured a stale reference.
    from ..deps import get_settings

    settings = get_settings()
    return resolve_api_key(provider, base_dir=settings.flows_dir)


def _resolve_llm_params(req: ConvertRequest) -> tuple[str, str | None, float, str]:
    """Return (provider, model, temperature, api_key); raises ConfigurationError if key missing."""
    provider = (
        req.options.provider
        if req.options is not None and req.options.provider is not None
        else "anthropic"
    )
    model = (
        req.options.model
        if req.options is not None and req.options.model is not None
        else None
    )
    temperature = (
        req.options.temperature
        if req.options is not None and req.options.temperature is not None
        else 0.0
    )
    api_key, _source = _resolve_api_key_for_request(provider)
    if not api_key:
        key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        raise ConfigurationError(
            f"LLM mode requires an API key for provider '{provider}'. "
            f"Set it via Settings → LLM Provider in the UI, or export "
            f"{key_env} in the API server environment."
        )
    return provider, model, temperature, api_key


def _count_ast_nodes(code: str) -> int:
    """Return the number of AST nodes in *code*; 0 on parse error."""
    try:
        tree = ast.parse(code)
        return sum(1 for _ in ast.walk(tree))
    except SyntaxError:
        return 0


def _emit_recipe_events(flow: Any, emitter: ConversionEventEmitter) -> None:
    """Walk a DataikuFlow and emit recipe_created / processor_added synthetic events."""
    for recipe in flow.recipes:
        rtype = recipe.recipe_type
        recipe_type = rtype.value if hasattr(rtype, "value") else str(rtype)
        emitter.recipe_created(recipe_name=recipe.name, recipe_type=recipe_type)
        for idx, step in enumerate(getattr(recipe, "steps", [])):
            proc_type = (
                step.processor_type.value
                if hasattr(step.processor_type, "value")
                else str(step.processor_type)
            )
            emitter.processor_added(
                recipe_name=recipe.name,
                processor_type=proc_type,
                step_index=idx,
            )


def convert_streaming(req: ConvertRequest, emitter: ConversionEventEmitter) -> None:
    """Run a conversion and bridge milestones into *emitter*.

    This function is **synchronous** and intended to run in a worker thread
    via ``asyncio.to_thread``.  It emits synthetic milestones because py-iku
    does not yet expose fine-grained progress hooks at the recipe/processor
    level — only ``convert_with_llm`` offers an ``on_progress`` callback.

    Events emitted (rule mode):
        started → ast_parsed → recipe_created* → processor_added* → optimized → completed

    Events emitted (LLM mode):
        started → provider_call_started → provider_call_completed
        → recipe_created* → processor_added* → optimized → completed

    On any Py2DataikuError: emits ``error`` with RFC 7807 problem dict.
    """
    optimize = req.options.optimize if req.options is not None else True
    code_bytes = len(req.code.encode())

    emitter.started(mode=req.mode.value, code_size_bytes=code_bytes)

    try:
        if req.mode == ConvertMode.RULE:
            node_count = _count_ast_nodes(req.code)
            emitter.ast_parsed(node_count=node_count)

            flow = convert(req.code, optimize=optimize)

            _emit_recipe_events(flow, emitter)
            emitter.optimized(reduction_count=0)

        else:
            # LLM mode
            provider, model, temperature, api_key = _resolve_llm_params(req)

            emitter.provider_call_started(provider=provider, model=model)

            # on_progress callback phases:
            # "start","analyzing","analyzed","generating","optimizing","done"
            _llm_response_holder: dict[str, Any] = {}

            def _on_progress(phase: str, data: Any = None) -> None:  # noqa: ANN401
                pass  # future: emit finer-grained events per phase

            flow = convert_with_llm(
                req.code,
                provider=provider,
                api_key=api_key,
                model=model,
                optimize=optimize,
                temperature=temperature,
                on_progress=_on_progress,
            )

            emitter.provider_call_completed(provider=provider, model=model)

            _emit_recipe_events(flow, emitter)
            emitter.optimized(reduction_count=0)

    except Py2DataikuError as exc:
        logger.warning("Py2DataikuError in streaming conversion: %s", exc)
        emitter.error(problem_dict(exc, instance="/convert/stream"))
        return

    except Exception as exc:
        logger.exception("Unexpected error in streaming conversion: %s", exc)
        from py2dataiku.exceptions import ConversionError
        wrapped = ConversionError(str(exc))
        emitter.error(problem_dict(wrapped, instance="/convert/stream"))
        return

    # Build response models
    try:
        flow_dict = flow.to_dict()
        extra_warnings = _sanitize_flow_dict(flow_dict)
        flow_model = DataikuFlowModel.model_validate(flow_dict)
        score = score_flow(flow)
        score_updates: dict = {
            "recipe_count": len(flow_dict.get("recipes") or []),
            "dataset_count": len(flow_dict.get("datasets") or []),
        }
        llm_usage = getattr(flow, "llm_usage", None)
        if llm_usage:
            score_updates["usage"] = {
                "input_tokens": llm_usage.get("input_tokens"),
                "output_tokens": llm_usage.get("output_tokens"),
                "cache_read_input_tokens": llm_usage.get("cache_read_input_tokens"),
                "cache_creation_input_tokens": llm_usage.get(
                    "cache_creation_input_tokens"
                ),
            }
            in_tok = llm_usage.get("input_tokens") or 0
            out_tok = llm_usage.get("output_tokens") or 0
            cached = llm_usage.get("cache_read_input_tokens") or 0
            score_updates["cost_estimate"] = round(
                (in_tok * 3.0 + cached * 0.30 + out_tok * 15.0) / 1_000_000, 6
            )
        score = score.model_copy(update=score_updates)
        emitter.completed(
            flow=flow_model,
            score=score,
            warnings=list(flow.warnings) + extra_warnings,
        )
    except Exception as exc:
        logger.exception("Error building completion payload: %s", exc)
        from py2dataiku.exceptions import ConversionError
        wrapped = ConversionError(str(exc))
        emitter.error(problem_dict(wrapped, instance="/convert/stream"))
