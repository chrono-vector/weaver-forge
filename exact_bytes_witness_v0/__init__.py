"""Exact-bytes Ed25519 witness checks.

A success string is one pinned signature check. It is not trust,
identity, evidence, or authority.
"""

from exact_bytes_witness_v0.verify import (
    ExactBytesWitnessError,
    verify_exact_bytes_witness,
)

__all__ = [
    "ExactBytesWitnessError",
    "verify_exact_bytes_witness",
]
