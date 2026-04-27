"""Security primitives for py-iku Studio API (M7).

* ``share_links`` — HMAC-signed share-link tokens (sign/verify).
* ``secrets`` — KMS-ready secrets-provider interface and an env-var
  default implementation.
"""

from .secrets import (
    EnvSecretsProvider,
    KmsSecretsProvider,
    SecretsProvider,
)
from .share_links import (
    InvalidShareToken,
    SharePayload,
    sign,
    verify,
)

__all__ = [
    "EnvSecretsProvider",
    "InvalidShareToken",
    "KmsSecretsProvider",
    "SecretsProvider",
    "SharePayload",
    "sign",
    "verify",
]
