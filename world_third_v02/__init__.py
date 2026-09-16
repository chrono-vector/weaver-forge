"""WORLD THIRD v0.2 — Weaver-side additive artifact families.

VERIFY-only. Not IW acceptance. Not Human acceptance. Not canonical.
Not publication. Not authorization. Not Job Agent Work Trace bridge.
"""

from .verification_ref_v0 import (
    ARTIFACT_CLASS,
    ARTIFACT_TYPE,
    NONCLAIMS,
    SCHEMA_ID,
    SCHEMA_VERSION,
    VERIFICATION_RESULTS,
    WorldThirdVerificationRefError,
    build_verification_ref_v0,
    resolve_verification_ref_v0,
    validate_verification_ref_v0,
    verification_ref_content_sha256,
)

__all__ = [
    "ARTIFACT_CLASS",
    "ARTIFACT_TYPE",
    "NONCLAIMS",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "VERIFICATION_RESULTS",
    "WorldThirdVerificationRefError",
    "build_verification_ref_v0",
    "resolve_verification_ref_v0",
    "validate_verification_ref_v0",
    "verification_ref_content_sha256",
]
