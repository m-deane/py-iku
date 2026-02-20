"""LLM provider abstractions for py2dataiku."""

import json
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


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
    usage: Optional[Dict[str, int]] = None
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
    ) -> Dict[str, Any]:
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
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                kwargs: Dict[str, Any] = {"api_key": self.api_key, "max_retries": self.max_retries}
                if self.timeout is not None:
                    kwargs["timeout"] = self.timeout
                self._client = anthropic.Anthropic(**kwargs)
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
        return self._client

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send a completion request to Claude."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw_response=response,
        )

    def complete_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
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
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            try:
                import openai
                kwargs: Dict[str, Any] = {"api_key": self.api_key, "max_retries": self.max_retries}
                if self.timeout is not None:
                    kwargs["timeout"] = self.timeout
                self._client = openai.OpenAI(**kwargs)
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai"
                )
        return self._client

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        """Send a completion request to GPT."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
        )

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
    ) -> Dict[str, Any]:
        """Send a completion request with JSON mode."""
        messages = []
        json_system = (system_prompt or "") + "\n\nYou must respond with valid JSON only."
        messages.append({"role": "system", "content": json_system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=messages,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        return json.loads(content)

    @property
    def model_name(self) -> str:
        return self.model


class MockProvider(LLMProvider):
    """Mock provider for testing without API calls."""

    def __init__(self, responses: Optional[Dict[str, str]] = None):
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
    ) -> Dict[str, Any]:
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
) -> LLMProvider:
    """
    Factory function to get an LLM provider.

    Args:
        provider: Provider name ("anthropic", "openai", "mock")
        api_key: API key (uses environment variable if not provided)
        model: Model name (uses provider default if not provided)

    Returns:
        LLMProvider instance
    """
    if provider == "anthropic":
        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        return AnthropicProvider(**kwargs)
    elif provider == "openai":
        kwargs = {"api_key": api_key}
        if model:
            kwargs["model"] = model
        return OpenAIProvider(**kwargs)
    elif provider == "mock":
        return MockProvider()
    else:
        raise ValueError(f"Unknown provider: {provider}")
