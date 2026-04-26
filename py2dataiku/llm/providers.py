"""LLM provider abstractions for py2dataiku."""

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from py2dataiku.exceptions import ConfigurationError

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n?(.*?)```", re.DOTALL)


def _extract_json(text: str) -> str:
    """Extract JSON content from an LLM response, handling code blocks."""
    text = text.strip()
    # Try to find JSON inside a code block first
    match = _JSON_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    # Already bare JSON
    return text


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    # Values may be int or None — cache_creation_input_tokens / cache_read_input_tokens
    # are None when caching is disabled or unsupported by the SDK version.
    usage: Optional[dict[str, Optional[int]]] = None
    raw_response: Optional[Any] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send a completion request to the LLM."""
        pass

    @abstractmethod
    def complete_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """Send a completion request and parse JSON response."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the model name."""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        temperature: float = 0.0,
        disable_cache: bool = False,
    ):
        """Initialize the Anthropic Claude provider.

        Args:
            api_key: Anthropic API key. Falls back to the
                ``ANTHROPIC_API_KEY`` environment variable when ``None``.
            model: Claude model ID to use (default:
                ``"claude-sonnet-4-20250514"``).
            max_tokens: Maximum tokens in the completion response
                (default: ``4096``).
            timeout: HTTP request timeout in seconds. ``None`` uses the
                Anthropic SDK default (no explicit timeout).
            max_retries: Number of automatic retries on transient errors
                (default: ``2``).
            temperature: Sampling temperature (default: ``0.0``). Keep at
                ``0.0`` for deterministic, reproducible flow conversions.
                The wave-A determinism prober found the original default of
                ``1.0`` produced run-to-run drift (e.g. varying intermediate
                dataset names for the same input code).
            disable_cache: When ``True``, the system prompt is sent as a
                plain string instead of a structured block with
                ``cache_control: ephemeral``. Useful in tests or when you
                want to avoid dependency on Anthropic's 5-minute cache
                state. When ``False`` (default) the prompt cache can reduce
                per-call token cost by 70-80% for repeated sessions.

        Raises:
            ConfigurationError: If no API key is found (neither argument
                nor environment variable).
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter. (Or use the rule-based convert() instead.)"
            )
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        # Default to 0.0 — code-to-flow conversion is a structured extraction
        # task where determinism (same code -> same flow) matters more than
        # creativity. Wave A determinism prober found temperature default 1.0
        # was the dominant source of run-to-run drift (e.g. dropna() inventing
        # `df_temp`/`df_initial` intermediate dataset names).
        self.temperature = temperature
        # When True, fall back to the legacy string `system=...` form. Useful
        # for tests or when callers don't want the API to depend on the 5-min
        # ephemeral-cache state on the server side.
        self.disable_cache = disable_cache
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                kwargs: dict[str, Any] = {"api_key": self.api_key, "max_retries": self.max_retries}
                if self.timeout is not None:
                    kwargs["timeout"] = self.timeout
                self._client = anthropic.Anthropic(**kwargs)
            except ImportError as e:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                ) from e
        return self._client

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send a completion request to Claude.

        When ``system_prompt`` is non-empty, it's passed as a structured block
        with ``cache_control: ephemeral`` so the Anthropic API caches it for
        ~5 minutes. Subsequent calls within that window with an identical
        system prompt only pay ~10% of the input-token cost for the cached
        portion, cutting LLM-path cost by 70-80% for typical multi-call
        sessions. Set ``disable_cache=True`` on the provider to fall back to
        the legacy string form (e.g. for tests).
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
            "temperature": self.temperature,
        }
        if system_prompt:
            if self.disable_cache:
                kwargs["system"] = system_prompt
            else:
                kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]

        response = self.client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                # Cache hit/miss tracking. Anthropic SDK returns these as None
                # when caching is disabled or for non-cached portions; older
                # SDKs may not expose these attributes at all (hence getattr).
                "cache_creation_input_tokens": getattr(
                    response.usage, "cache_creation_input_tokens", None
                ),
                "cache_read_input_tokens": getattr(
                    response.usage, "cache_read_input_tokens", None
                ),
            },
            raw_response=response,
        )

    def complete_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """Send a completion request and parse JSON response."""
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\n\nYou must respond with valid JSON only. No other text."

        response = self.complete(prompt, json_system)
        content = _extract_json(response.content)
        return json.loads(content)

    @property
    def model_name(self) -> str:
        return self.model


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        max_tokens: int = 4096,
        timeout: Optional[float] = None,
        max_retries: int = 2,
        temperature: float = 0.0,
        seed: Optional[int] = 42,
    ):
        """Initialize the OpenAI GPT provider.

        Args:
            api_key: OpenAI API key. Falls back to the ``OPENAI_API_KEY``
                environment variable when ``None``.
            model: OpenAI model ID to use (default: ``"gpt-4o"``).
            max_tokens: Maximum tokens in the completion response
                (default: ``4096``).
            timeout: HTTP request timeout in seconds. ``None`` uses the
                OpenAI SDK default.
            max_retries: Number of automatic retries on transient errors
                (default: ``2``).
            temperature: Sampling temperature (default: ``0.0``). Keep at
                ``0.0`` for deterministic, reproducible flow conversions.
                Same rationale as :class:`AnthropicProvider`.
            seed: Integer seed forwarded to the OpenAI API for additional
                determinism (default: ``42``). Pass ``None`` to omit it.

        Raises:
            ConfigurationError: If no API key is found (neither argument
                nor environment variable).
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter. (Or use the rule-based convert() instead.)"
            )
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        # Determinism defaults — same rationale as AnthropicProvider.
        # OpenAI also accepts a `seed` for further determinism.
        self.temperature = temperature
        self.seed = seed
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                kwargs: dict[str, Any] = {"api_key": self.api_key, "max_retries": self.max_retries}
                if self.timeout is not None:
                    kwargs["timeout"] = self.timeout
                self._client = openai.OpenAI(**kwargs)
            except ImportError as e:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                ) from e
        return self._client

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send a completion request to GPT."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.seed is not None:
            kwargs["seed"] = self.seed

        response = self.client.chat.completions.create(**kwargs)

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
            raw_response=response,
        )

    def complete_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """Send a completion request with JSON mode."""
        messages = []
        json_system = (system_prompt or "") + "\n\nYou must respond with valid JSON only."
        messages.append({"role": "system", "content": json_system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": self.temperature,
        }
        if self.seed is not None:
            kwargs["seed"] = self.seed

        response = self.client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content
        return json.loads(content)

    @property
    def model_name(self) -> str:
        return self.model


class MockProvider(LLMProvider):
    """Mock provider for testing without API calls."""

    def __init__(self, responses: Optional[dict[str, str]] = None):
        """Initialize the mock provider.

        Args:
            responses: Optional mapping of prompt substring to canned
                response text. When a prompt contains a key from this dict
                that response is returned; otherwise a default empty-steps
                JSON blob is used. Calls are recorded in ``self.calls``.
        """
        self.responses = responses or {}
        self.calls = []

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Return mock response."""
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})

        # Check for matching response
        for key, response in self.responses.items():
            if key in prompt:
                return LLMResponse(content=response, model="mock")

        # Default response
        return LLMResponse(
            content='{"steps": [], "datasets": [], "code_summary": "Mock analysis"}',
            model="mock",
        )

    def complete_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> dict[str, Any]:
        """Return mock JSON response."""
        response = self.complete(prompt, system_prompt)
        return json.loads(response.content)

    @property
    def model_name(self) -> str:
        return "mock"


def get_provider(
    provider: str = "anthropic",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> LLMProvider:
    """
    Factory function to get an LLM provider.

    Args:
        provider: Provider name ("anthropic", "openai", "mock")
        api_key: API key (uses environment variable if not provided)
        model: Model name (uses provider default if not provided)
        temperature: Sampling temperature override (default: 0.0 — see
            AnthropicProvider/OpenAIProvider __init__ for rationale).

    Returns:
        LLMProvider instance
    """
    if provider == "anthropic":
        kwargs: dict[str, Any] = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        if temperature is not None:
            kwargs["temperature"] = temperature
        return AnthropicProvider(**kwargs)
    elif provider == "openai":
        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        if temperature is not None:
            kwargs["temperature"] = temperature
        return OpenAIProvider(**kwargs)
    elif provider == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unknown provider: {provider}")
