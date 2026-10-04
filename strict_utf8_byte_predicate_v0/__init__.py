"""Strict UTF-8 byte predicates for one code-owned grammar fact.

A returned record is not an evidence kind, authority, admission, or support.
"""

from strict_utf8_byte_predicate_v0.record import (
    SubpError,
    parse_subp,
    produce_subp,
    subp_reproduced_from_supplied_inputs,
    subp_structurally_consistent,
)

__all__ = [
    "SubpError",
    "produce_subp",
    "parse_subp",
    "subp_structurally_consistent",
    "subp_reproduced_from_supplied_inputs",
]
