"""Explain-this-recipe service — prompts the LLM, caches results on disk.

Cache behaviour
---------------
The cache is a small append-only JSONL file at
``Settings.flows_dir / explain-cache.jsonl``. Each line is::

    {"key": "<sha256>", "recipe_type": "GROUPING", "value": {...response...}}

Lookups walk newest → oldest so a freshly-written entry shadows any earlier
one with the same key. Identical recipe shapes (same canonical type +
normalised settings hash) hit the cache without an LLM call; different
settings miss and pay one LLM round-trip.

LLM prompt
----------
The prompt is deliberately small and asks for a JSON-only response with the
three popover fields. The trading-desk persona is baked into the rubric so
explanations land in the right register — "EOD MtM rollups", "tenor curves",
"settle-window deploys" are first-class vocabulary.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Optional

from py2dataiku.exceptions import ConfigurationError, Py2DataikuError
from py2dataiku.llm.providers import (
    LLMProvider,
    MockProvider,
    get_provider,
)

from ..schemas.explain import ExplainRecipeRequest, ExplainRecipeResponse
from .llm_audit import estimate_cost_usd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache key
# ---------------------------------------------------------------------------


_DROPPED_KEYS = {
    # These fields are noise — we don't want a confidence wobble or a name
    # rename to bust the cache. Recipe shape is what matters.
    "name",
    "confidence",
    "reasoning",
    "source_lines",
    "inputs",
    "outputs",
}


def _normalise(value: Any) -> Any:
    """Stable, order-independent normalisation for cache hashing."""
    if isinstance(value, dict):
        return {
            k: _normalise(v)
            for k, v in sorted(value.items())
            if k not in _DROPPED_KEYS
        }
    if isinstance(value, list):
        return [_normalise(v) for v in value]
    return value


def recipe_cache_key(recipe: dict[str, Any]) -> tuple[str, str]:
    """Return ``(recipe_type, sha256_key)`` for the given recipe dict.

    The key collapses across superficial differences — name, confidence,
    reasoning, IO names — so renaming a recipe doesn't blow up the cache.
    Settings, processor steps, and the canonical ``type`` field are
    fully captured.
    """
    recipe_type = str(recipe.get("type", "UNKNOWN")).upper()
    normalised = _normalise(recipe)
    blob = json.dumps(normalised, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return recipe_type, f"{recipe_type}:{digest[:32]}"


# ---------------------------------------------------------------------------
# On-disk cache
# ---------------------------------------------------------------------------


class ExplainCache:
    """Thread-safe append-only JSONL cache of explain-recipe results."""

    FILENAME = "explain-cache.jsonl"

    def __init__(self, base_dir: Path | str) -> None:
        self._base_dir = Path(base_dir)
        self._path = self._base_dir / self.FILENAME
        self._lock = threading.Lock()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    @property
    def path(self) -> Path:
        return self._path

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """Return the latest cached value for *key*, or None on miss."""
        if not self._path.exists():
            return None
        with self._lock:
            try:
                with self._path.open("r", encoding="utf-8") as fh:
                    lines = fh.readlines()
            except OSError:
                return None
        # Walk newest → oldest so an updated entry wins.
        for raw in reversed(lines):
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if row.get("key") == key:
                value = row.get("value")
                if isinstance(value, dict):
                    return value
        return None

    def put(self, key: str, recipe_type: str, value: dict[str, Any]) -> None:
        line = json.dumps(
            {"key": key, "recipe_type": recipe_type, "value": value},
            separators=(",", ":"),
        )
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
                fh.flush()


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


SYSTEM_RUBRIC = """You are an assistant embedded in py-iku Studio, a tool that
converts pandas/numpy/sklearn pipelines to Dataiku DSS flows. You are
explaining a single recipe to a front-office data engineer at an oil/gas/power
trading desk.

Output rules:
1. Respond with a SINGLE JSON object — no prose before or after.
2. Keys: "what_this_does", "trading_context", "watch_out_for".
3. Each value is exactly one sentence. Plain English. ≤ 32 words each.
4. Use textbook DSS terminology: "PREPARE recipe", "GROUPING recipe", "JOIN
   recipe", "WINDOW recipe", "TOP_N recipe", "SPLIT recipe", "processor".
5. The trading_context line must mention a concrete front-office workflow:
   EOD MtM rollups, tenor/curve construction, P&L attribution, basis trades,
   crack/heat-rate/freight calculations, settle-window deploys, ISO LMP
   aggregation, counterparty curve diff, position blotters, etc.
6. The watch_out_for line names a real pitfall (empty partition_columns,
   timezone drift on settle dates, fan-out before a JOIN, FILL_EMPTY masking
   missing trade-capture rows, etc.).
"""


def _summarise_recipe(recipe: dict[str, Any]) -> str:
    rid = recipe.get("name", "(unnamed)")
    rtype = recipe.get("type", "?")
    inputs = ",".join(recipe.get("inputs", []) or [])
    outputs = ",".join(recipe.get("outputs", []) or [])
    lines = [
        f"RECIPE: {rid} :: {rtype}",
        f"  in=[{inputs}]  out=[{outputs}]",
    ]
    settings = recipe.get("settings")
    if isinstance(settings, dict) and settings:
        # Trim to keep the prompt small — full settings rarely change the gist.
        compact = json.dumps(settings, separators=(",", ":"))[:1500]
        lines.append(f"  settings: {compact}")
    steps = recipe.get("steps") or []
    if steps:
        ptypes = [str(s.get("processor_type", "?")) for s in steps[:12]]
        extra = "..." if len(steps) > 12 else ""
        lines.append(f"  processors: {', '.join(ptypes)}{extra}")
    return "\n".join(lines)


def build_explain_prompts(req: ExplainRecipeRequest) -> tuple[str, str]:
    """Return ``(system_prompt, user_prompt)`` for the LLM call."""
    summary = _summarise_recipe(req.recipe)
    ctx_block = ""
    if req.context:
        ctx_compact = json.dumps(req.context, separators=(",", ":"))[:1500]
        ctx_block = f"\n\n--- SURROUNDING FLOW CONTEXT ---\n{ctx_compact}"

    system = SYSTEM_RUBRIC + "\n\n--- RECIPE UNDER REVIEW ---\n" + summary + ctx_block
    user = (
        "Explain this recipe in three single-sentence bullets, returning the "
        "JSON object specified above. No markdown."
    )
    return system.strip(), user.strip()


# ---------------------------------------------------------------------------
# Provider resolution (mirrors chat.resolve_provider — env-only key lookup)
# ---------------------------------------------------------------------------


def resolve_provider(
    provider: str,
    model: Optional[str] = None,
) -> LLMProvider:
    """Return an LLMProvider, honouring env-only API key resolution.

    Tests pass ``provider="mock"`` to skip the network entirely.
    """
    if provider == "mock":
        return MockProvider()
    key_env = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ConfigurationError(
            f"explain-recipe requires {key_env} to be set in the API server "
            "environment."
        )
    return get_provider(provider=provider, api_key=api_key, model=model)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


_REQUIRED_FIELDS = ("what_this_does", "trading_context", "watch_out_for")


def parse_explain_payload(content: str) -> dict[str, str]:
    """Pull the three-field JSON object out of an LLM response.

    Tolerates leading/trailing prose, code fences, or stray whitespace — we
    look for the first ``{`` and the matching closing brace and parse that.
    Raises ``Py2DataikuError`` if any required field is missing.
    """
    raw = content.strip()
    if raw.startswith("```"):
        # Strip a fenced code block — markdown-prone providers sometimes emit one.
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise Py2DataikuError("explain-recipe response did not contain JSON.")
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise Py2DataikuError(
            f"explain-recipe response was not valid JSON: {exc}"
        ) from exc
    out: dict[str, str] = {}
    for field in _REQUIRED_FIELDS:
        value = parsed.get(field)
        if not isinstance(value, str) or not value.strip():
            raise Py2DataikuError(
                f"explain-recipe response missing required field: {field}"
            )
        out[field] = value.strip()
    return out


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def explain_recipe(
    req: ExplainRecipeRequest,
    cache: ExplainCache,
    provider: Optional[LLMProvider] = None,
) -> ExplainRecipeResponse:
    """Resolve a recipe explanation, hitting the cache when possible.

    A successful call writes the response to the cache before returning so
    a subsequent identical request (same canonical recipe shape) skips the
    LLM entirely.
    """
    recipe_type, key = recipe_cache_key(req.recipe)
    cached = cache.get(key)
    if cached is not None:
        return ExplainRecipeResponse(
            what_this_does=str(cached.get("what_this_does", "")),
            trading_context=str(cached.get("trading_context", "")),
            watch_out_for=str(cached.get("watch_out_for", "")),
            recipe_type=recipe_type,
            cache_key=key,
            cache_hit=True,
            model=str(cached.get("model", "")),
            usage={},
            cost_usd=0.0,
        )

    prov = provider or resolve_provider(req.provider, req.model)
    system, user = build_explain_prompts(req)
    resp = prov.complete(prompt=user, system_prompt=system)
    parsed = parse_explain_payload(resp.content)

    usage = resp.usage or {}
    p_tok = int(usage.get("input_tokens", 0) or 0)
    c_tok = int(usage.get("output_tokens", 0) or 0)
    model_name = resp.model or prov.model_name
    cost = estimate_cost_usd(model_name, p_tok, c_tok)

    payload = ExplainRecipeResponse(
        what_this_does=parsed["what_this_does"],
        trading_context=parsed["trading_context"],
        watch_out_for=parsed["watch_out_for"],
        recipe_type=recipe_type,
        cache_key=key,
        cache_hit=False,
        model=model_name,
        usage={"input_tokens": p_tok, "output_tokens": c_tok},
        cost_usd=cost,
    )
    cache.put(
        key,
        recipe_type,
        {
            "what_this_does": payload.what_this_does,
            "trading_context": payload.trading_context,
            "watch_out_for": payload.watch_out_for,
            "model": model_name,
        },
    )
    return payload
