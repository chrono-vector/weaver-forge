"""Domain-separated digests for future additive packages.

A returned hex string is not comparable to a legacy untagged digest.
"""

from domain_separated_digest_v0.digest import (
    DomainSeparatedDigestError,
    digest_presented_subject_bytes,
    digest_r4_claim_body,
    domain_separated_digest,
)

__all__ = [
    "DomainSeparatedDigestError",
    "digest_presented_subject_bytes",
    "digest_r4_claim_body",
    "domain_separated_digest",
]
