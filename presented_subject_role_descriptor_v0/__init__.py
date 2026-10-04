"""Presented-subject role descriptors for one code-owned role.

A returned record is not authority, admission, or support.
"""

from presented_subject_role_descriptor_v0.record import (
    PsrdError,
    parse_psrd,
    produce_psrd,
    psrd_reproduced_from_supplied_inputs,
    psrd_structurally_consistent,
)

__all__ = [
    "PsrdError",
    "produce_psrd",
    "parse_psrd",
    "psrd_structurally_consistent",
    "psrd_reproduced_from_supplied_inputs",
]
