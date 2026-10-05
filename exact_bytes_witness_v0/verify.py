"""Exact-bytes Ed25519 witness verification v0.

EXACT_BYTES_WITNESS_VALID means the pinned pure-Ed25519 verifier accepted
this 32-byte public key, this 64-byte signature, and these exact message
bytes. It does not establish a trusted key, signer identity, authorization,
independence, creator, provenance, timestamp, freshness, anti-replay,
evidence, evidence kind, truth, support, relevance, sufficiency,
completeness, admission, authority, correspondence, or Human Final.
"""

from __future__ import annotations

_SUCCESS = "EXACT_BYTES_WITNESS_VALID"
_FAILURE = "EXACT_BYTES_WITNESS_REJECTED"
_CRYPTOGRAPHY_VERSION = "50.0.2"
_CFFI_VERSION = "2.1.1"
_PYCPARSER_VERSION = "3.0"


class ExactBytesWitnessError(Exception):
    """Closed failure of one exact-bytes witness check."""

    def __init__(self) -> None:
        self.code = _FAILURE
        super().__init__(self.code)


def _reject() -> None:
    raise ExactBytesWitnessError() from None


def verify_exact_bytes_witness(
    public_key: bytes, signature: bytes, message: bytes
) -> str:
    """Verify one raw Ed25519 tuple under the frozen profile.

    The three arguments are exact builtin bytes. The message is the
    verifier data argument, unchanged.
    """
    if (
        type(public_key) is not bytes
        or type(signature) is not bytes
        or type(message) is not bytes
    ):
        _reject()
    if len(public_key) != 32 or len(signature) != 64:
        _reject()
    try:
        from importlib.metadata import version
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )

        if version("cryptography") != _CRYPTOGRAPHY_VERSION:
            _reject()
        if version("cffi") != _CFFI_VERSION:
            _reject()
        if version("pycparser") != _PYCPARSER_VERSION:
            _reject()
        key = Ed25519PublicKey.from_public_bytes(public_key)
        verified = key.verify(signature, message)
    except ExactBytesWitnessError:
        raise
    except Exception:
        raise ExactBytesWitnessError() from None
    if verified is not None:
        _reject()
    return _SUCCESS


__all__ = [
    "ExactBytesWitnessError",
    "verify_exact_bytes_witness",
]
