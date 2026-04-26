"""Pluggable secrets-provider interface.

py-iku Studio M7 ships two implementations:

* :class:`EnvSecretsProvider` — reads from ``os.environ``.
* :class:`KmsSecretsProvider` — placeholder that always raises
  :class:`NotImplementedError`; ready to be wired up in a follow-up
  milestone behind a real KMS client.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod


class SecretsProvider(ABC):
    """Look up named secrets at runtime."""

    @abstractmethod
    def get(self, name: str) -> str:
        """Return the secret stored under *name*; raise on miss."""


class EnvSecretsProvider(SecretsProvider):
    """Read secrets from the process environment."""

    def __init__(self, prefix: str = "") -> None:
        self._prefix = prefix

    def get(self, name: str) -> str:
        env_key = f"{self._prefix}{name}" if self._prefix else name
        value = os.environ.get(env_key)
        if value is None:
            raise KeyError(f"Secret '{env_key}' is not set in the environment")
        return value


class KmsSecretsProvider(SecretsProvider):
    """Placeholder for an upcoming KMS-backed implementation."""

    def __init__(self, *_: object, **__: object) -> None:  # noqa: D401
        # Accept arbitrary args so callers can pre-wire config without
        # blowing up on instantiation.  The error fires on first ``get``.
        pass

    def get(self, name: str) -> str:  # pragma: no cover — unreachable
        raise NotImplementedError(
            "KmsSecretsProvider is not yet implemented. "
            "Wire a KMS client behind this stub before enabling it."
        )
