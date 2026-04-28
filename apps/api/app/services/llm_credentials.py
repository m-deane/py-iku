"""LLM credential persistence — single-user, plaintext-on-disk store.

The Studio runs locally for one user at a time, so we deliberately accept the
trade-off of plaintext-on-disk storage in exchange for a one-click "set my key"
UX. The constraints — visible in :class:`LlmCredentialStore` — are:

* keys live ONLY in ``Settings.flows_dir / llm-credentials.json``;
* the on-disk file is created with mode 0600 (POSIX) so it is readable only by
  the running user;
* the key is **never** echoed back to clients — :meth:`status` is the only
  read API and returns a boolean.

Resolution order at request time:

1. file (``LlmCredentialStore.get_key``) — wins when present.
2. env (``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY``) — fallback for users who
   prefer the server-env workflow.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)


SUPPORTED_PROVIDERS: tuple[str, ...] = ("anthropic", "openai")
ProviderName = Literal["anthropic", "openai"]


def _env_var_for(provider: str) -> str:
    """Return the canonical environment variable name for *provider*."""
    return "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"


@dataclass(frozen=True)
class CredentialState:
    """What the UI needs to know — never the key itself."""

    provider: str
    has_key: bool
    source: Literal["file", "env", "none"]
    model: str | None = None


class LlmCredentialStore:
    """JSON-on-disk credential cache. Thread-safe for the single-process Studio."""

    FILENAME = "llm-credentials.json"

    def __init__(self, base_dir: Path | str) -> None:
        self._base_dir = Path(base_dir)
        self._path = self._base_dir / self.FILENAME
        self._lock = threading.Lock()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def _load(self) -> dict[str, dict[str, str]]:
        if not self._path.exists():
            return {}
        try:
            with self._lock, self._path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                return {}
            # Filter out non-dict provider entries (defensive — file was
            # written by a previous version of this code, or a human edit).
            return {
                k: v for k, v in data.items() if isinstance(v, dict)
            }
        except (OSError, json.JSONDecodeError):
            logger.warning(
                "LLM credentials file unreadable; treating as empty",
                extra={"path": str(self._path)},
            )
            return {}

    def get_key(self, provider: str) -> str | None:
        """Return the persisted key for *provider*, or None."""
        data = self._load()
        entry = data.get(provider) or {}
        key = entry.get("key")
        if isinstance(key, str) and key:
            return key
        return None

    def get_model(self, provider: str) -> str | None:
        data = self._load()
        entry = data.get(provider) or {}
        model = entry.get("model")
        if isinstance(model, str) and model:
            return model
        return None

    def status(self, provider: str) -> CredentialState:
        """Return a :class:`CredentialState` summarising file + env-var."""
        if provider not in SUPPORTED_PROVIDERS:
            return CredentialState(
                provider=provider, has_key=False, source="none"
            )
        file_key = self.get_key(provider)
        if file_key:
            return CredentialState(
                provider=provider,
                has_key=True,
                source="file",
                model=self.get_model(provider),
            )
        env_key = os.environ.get(_env_var_for(provider))
        if env_key:
            return CredentialState(
                provider=provider, has_key=True, source="env"
            )
        return CredentialState(
            provider=provider, has_key=False, source="none"
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def set_key(
        self, provider: str, key: str, *, model: str | None = None
    ) -> None:
        """Persist *key* (and optional *model*) for *provider*."""
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider {provider!r}")
        if not key:
            raise ValueError("key must be non-empty")
        with self._lock:
            data = self._load()
            entry = dict(data.get(provider) or {})
            entry["key"] = key
            if model is not None:
                entry["model"] = model
            data[provider] = entry
            self._write(data)

    def clear_key(self, provider: str) -> bool:
        """Remove the persisted entry for *provider*; return True if removed."""
        with self._lock:
            data = self._load()
            if provider not in data:
                return False
            data.pop(provider, None)
            self._write(data)
            return True

    def _write(self, data: dict[str, dict[str, str]]) -> None:
        # Write to a temp file then rename so a crash mid-write never leaves
        # the credentials file half-formed.
        tmp = self._path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        # Tighten perms before swapping in. On non-POSIX (Windows) this is a
        # best-effort no-op.
        try:
            os.chmod(tmp, 0o600)
        except OSError:  # pragma: no cover — Windows / read-only FS
            pass
        tmp.replace(self._path)


# ---------------------------------------------------------------------------
# Resolution helper used by /convert and friends
# ---------------------------------------------------------------------------


def resolve_api_key(
    provider: str, *, base_dir: Path | str | None = None
) -> tuple[str | None, Literal["file", "env", "none"]]:
    """Return ``(api_key, source)`` for *provider*.

    File takes precedence over env; both can be absent — the caller raises
    :class:`py2dataiku.exceptions.ConfigurationError` in that case so the
    error trickles up as RFC 7807.
    """
    if base_dir is not None:
        store = LlmCredentialStore(base_dir=base_dir)
        file_key = store.get_key(provider)
        if file_key:
            return file_key, "file"
    env_key = os.environ.get(_env_var_for(provider))
    if env_key:
        return env_key, "env"
    return None, "none"
