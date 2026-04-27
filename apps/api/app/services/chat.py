"""Chat-with-flow service — builds prompts, calls the LLM, parses citations."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Optional

from py2dataiku.exceptions import ConfigurationError
from py2dataiku.llm.providers import (
    LLMProvider,
    MockProvider,
    get_provider,
)

from ..schemas.chat import ChatCitation, ChatMessage, ChatRequest, ChatResponse
from .llm_audit import estimate_cost_usd

logger = logging.getLogger(__name__)


# -- Prompt construction ----------------------------------------------------


_RECIPE_CITE_RE = re.compile(r"\[recipe:([A-Za-z0-9_\-]+)\]")


SYSTEM_RUBRIC = """You are an assistant embedded in py-iku Studio, a tool that converts
pandas/numpy/sklearn pipelines to Dataiku DSS flows. You are answering questions
from a front-office data engineer at an oil/gas/power trading desk.

Rules you must follow:
1. Cite the specific recipe(s) you reference using the marker `[recipe:RECIPE_NAME]`
   exactly as the recipe is named in the supplied flow JSON. The frontend uses
   these markers to highlight nodes on the canvas.
2. Use the textbook terminology: "PREPARE recipe", "GROUPING recipe", "JOIN
   recipe", "WINDOW recipe", "TOP_N recipe", "SPLIT recipe", "processor"
   (a step inside PREPARE), "DAG", "fan-out".
3. When the user asks "why is recipe N medium-confidence?", read the recipe's
   `confidence` field if present, otherwise say it isn't surfaced in the flow.
4. Decline to speculate beyond what the flow JSON or the original pandas
   source contains. If the answer would require running the flow or guessing
   about data, say so plainly and stop.
5. When asked to rewrite in plain SQL, produce ANSI SQL that mirrors the
   recipe order. Do NOT invent column types — use the schema names from the
   flow when present.
6. Keep replies concise and terminal-friendly (≤6 short paragraphs).
"""


def _summarise_flow(flow: dict[str, Any]) -> str:
    """Return a compact textual summary of the flow JSON for the system prompt."""
    name = flow.get("flow_name", "(unnamed)")
    recipes = flow.get("recipes", []) or []
    datasets = flow.get("datasets", []) or []
    lines = [
        f"FLOW: {name}",
        f"  datasets ({len(datasets)}): "
        + ", ".join(str(d.get("name")) for d in datasets[:30]),
        f"  recipes ({len(recipes)}):",
    ]
    for r in recipes:
        rid = r.get("name", "?")
        rtype = r.get("type", "?")
        inputs = ",".join(r.get("inputs", []) or [])
        outputs = ",".join(r.get("outputs", []) or [])
        conf = r.get("confidence")
        conf_str = f" confidence={conf}" if conf is not None else ""
        lines.append(f"   - {rid} :: {rtype}  in=[{inputs}] out=[{outputs}]{conf_str}")
        steps = r.get("steps") or []
        if steps:
            ptypes = [str(s.get("processor_type", "?")) for s in steps[:10]]
            extra = "..." if len(steps) > 10 else ""
            lines.append(f"       steps: {', '.join(ptypes)}{extra}")
    return "\n".join(lines)


def build_prompts(req: ChatRequest) -> tuple[str, str]:
    """Return ``(system_prompt, user_prompt)`` ready to send to a provider."""
    flow_summary = _summarise_flow(req.flow_json)
    flow_json_excerpt = json.dumps(req.flow_json, separators=(",", ":"))[:8000]

    pandas_excerpt = (req.pandas_source or "").strip()
    if len(pandas_excerpt) > 4000:
        pandas_excerpt = pandas_excerpt[:4000] + "\n# ... truncated ...\n"

    system = (
        SYSTEM_RUBRIC
        + "\n\n--- FLOW SUMMARY ---\n"
        + flow_summary
        + "\n\n--- FLOW JSON (truncated) ---\n"
        + flow_json_excerpt
    )
    if pandas_excerpt:
        system += "\n\n--- ORIGINAL PANDAS SOURCE (truncated) ---\n" + pandas_excerpt

    history_block = ""
    if req.history:
        rendered = []
        for msg in req.history[-10:]:
            rendered.append(f"{msg.role.upper()}: {msg.content}")
        history_block = "\n\nPRIOR TURNS (most recent last):\n" + "\n".join(rendered)

    user = (
        history_block
        + "\n\nQUESTION:\n"
        + req.question
        + "\n\nReturn a focused answer, citing recipes with the [recipe:NAME] marker."
    )
    return system.strip(), user.strip()


# -- Citation extraction ----------------------------------------------------


def extract_citations(answer: str, flow: dict[str, Any]) -> list[ChatCitation]:
    """Pull `[recipe:NAME]` markers from *answer* and validate against flow recipes."""
    valid_names = {
        str(r.get("name")) for r in (flow.get("recipes") or []) if r.get("name")
    }
    citations: list[ChatCitation] = []
    seen: set[str] = set()
    for match in _RECIPE_CITE_RE.finditer(answer):
        rid = match.group(1)
        if rid in seen:
            continue
        seen.add(rid)
        # Only emit citations that point at a real recipe — stops the LLM from
        # making up nodes that don't exist on the canvas.
        if rid in valid_names:
            citations.append(ChatCitation(recipe_id=rid, source_lines=None))
    return citations


# -- Provider resolution ----------------------------------------------------


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
            f"Chat requires {key_env} to be set in the API server environment."
        )
    return get_provider(provider=provider, api_key=api_key, model=model)


# -- Sync answer ------------------------------------------------------------


def answer_chat(
    req: ChatRequest,
    provider: Optional[LLMProvider] = None,
) -> ChatResponse:
    """Run a single non-streaming chat turn and return the parsed response."""
    prov = provider or resolve_provider(req.provider, req.model)
    system, user = build_prompts(req)

    resp = prov.complete(prompt=user, system_prompt=system)
    answer = resp.content
    citations = extract_citations(answer, req.flow_json)

    usage = resp.usage or {}
    p_tok = int(usage.get("input_tokens", 0) or 0)
    c_tok = int(usage.get("output_tokens", 0) or 0)
    model_name = resp.model or prov.model_name
    cost = estimate_cost_usd(model_name, p_tok, c_tok)

    return ChatResponse(
        answer=answer,
        citations=citations,
        model=model_name,
        usage={
            "input_tokens": p_tok,
            "output_tokens": c_tok,
        },
        cost_usd=cost,
    )


def stream_chat_chunks(answer: str, *, chunk_size: int = 24):  # type: ignore[no-untyped-def]
    """Yield successive answer slices for SSE streaming.

    The two real providers expose token-level streaming, but for v1 we deliver
    a robust answer-then-chunk fallback so the wire protocol is identical
    regardless of provider. When real streaming arrives we replace this
    function with a true generator over provider-side deltas.
    """
    for i in range(0, len(answer), chunk_size):
        yield answer[i : i + chunk_size]
