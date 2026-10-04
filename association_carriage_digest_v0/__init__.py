"""Association-carriage digests for one code-owned tag.

A returned hex string is not comparable to a DSDS-v0 digest or a legacy
untagged digest.
"""

from association_carriage_digest_v0.digest import (
    AssociationCarriageDigestError,
    digest_association_carriage_preimage,
)

__all__ = [
    "AssociationCarriageDigestError",
    "digest_association_carriage_preimage",
]
