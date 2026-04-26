"""Tests for the secrets-provider abstraction (M7)."""

from __future__ import annotations

import pytest

from app.security.secrets import (
    EnvSecretsProvider,
    KmsSecretsProvider,
    SecretsProvider,
)


def test_env_secrets_provider_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PY_IKU_TEST_TOKEN", "supersecret")
    provider: SecretsProvider = EnvSecretsProvider()
    assert provider.get("PY_IKU_TEST_TOKEN") == "supersecret"


def test_env_secrets_provider_missing_key_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PY_IKU_TEST_NOPE", raising=False)
    provider = EnvSecretsProvider()
    with pytest.raises(KeyError):
        provider.get("PY_IKU_TEST_NOPE")


def test_env_secrets_provider_supports_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PY_IKU_TEST_KEY", "value")
    provider = EnvSecretsProvider(prefix="PY_IKU_TEST_")
    assert provider.get("KEY") == "value"


def test_kms_provider_get_raises_not_implemented() -> None:
    provider = KmsSecretsProvider()
    with pytest.raises(NotImplementedError):
        provider.get("any-key")
