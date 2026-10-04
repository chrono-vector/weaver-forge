"""Association Carriage Digest v0.

A digest is meaningful only together with the code-owned carriage tag.
Equal 64-hex strings are not semantic equality with DSDS-v0 digests,
untagged canonical digests, or file SHA-256.

Maximum meaning: the same tag and the same exact preimage bytes produce
the same SHA-256. This does not establish creator, time, order, truth,
support, admission, authority, or that a receipt was created.
"""

from __future__ import annotations

import hashlib

_TAG = b"weaver.acr.digest.v0\x00"


class AssociationCarriageDigestError(ValueError):
    """Closed failure while hashing an association-carriage preimage."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(message: str) -> None:
    raise AssociationCarriageDigestError("ACD_PREIMAGE_REJECTED", message)


def digest_association_carriage_preimage(preimage: bytes) -> str:
    """Hash one exact non-empty byte string under the carriage tag.

    The sole argument is the preimage. This function does not accept a
    domain, a prefix, or an expected digest, and it does not parse JSON.
    """
    if type(preimage) is not bytes:
        _fail("preimage must be exact bytes")
    if len(preimage) < 1:
        _fail("preimage is empty")
    return hashlib.sha256(_TAG + preimage).hexdigest()


__all__ = [
    "AssociationCarriageDigestError",
    "digest_association_carriage_preimage",
]
