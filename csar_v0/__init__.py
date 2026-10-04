"""Claim / subject association records for one frozen six-field schema.

A returned record is not authority, admission, or a legacy digest.
"""

from csar_v0.record import (
    CsarError,
    csar_reproduced_from_supplied_inputs,
    csar_structurally_consistent,
    parse_csar,
    produce_csar,
)

__all__ = [
    "CsarError",
    "produce_csar",
    "parse_csar",
    "csar_structurally_consistent",
    "csar_reproduced_from_supplied_inputs",
]
