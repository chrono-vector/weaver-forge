from __future__ import annotations

import types
import unittest
from pathlib import Path

from tools.ecp import checkpoint as ecp
from tools.ecp.test_checkpoint import HEAD, OTHER, checkpoint, digest


SOURCE = Path(ecp.__file__).read_text(encoding="utf-8")


def mutant(*replacements: tuple[str, str]):
    source = SOURCE
    for old, new in replacements:
        if source.count(old) != 1:
            raise AssertionError(f"mutation marker count is not one: {old!r}")
        source = source.replace(old, new)
    module = types.ModuleType("ecp_mutant")
    module.__file__ = str(Path(ecp.__file__))
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module


def verify(module, value=None, retained=None, **updates):
    record = value or checkpoint()
    if retained is None:
        retained = module.canonical_checkpoint_bytes(record)
    arguments = {
        "subject_log_id": "audit-main",
        "current_sequence": 120,
        "current_head_digest": digest(HEAD),
    }
    arguments.update(updates)
    return module.verify_checkpoint(record, retained, **arguments)


class ECPMutationTests(unittest.TestCase):
    def test_mutant_ignore_rollback_is_killed(self):
        module = mutant(("return LOCAL_HISTORY_BEHIND_CHECKPOINT\n    if current_sequence ==", "return CHECKPOINT_MATCH_CURRENT\n    if current_sequence =="))
        self.assertNotEqual(ecp.LOCAL_HISTORY_BEHIND_CHECKPOINT, verify(module, current_sequence=119, current_head_digest=digest(OTHER)))

    def test_mutant_ignore_committed_digest_mismatch_is_killed(self):
        module = mutant(("if current_digest == checkpoint_digest", "if True"))
        self.assertNotEqual(ecp.LINEAGE_MISMATCH, verify(module, current_head_digest=digest(OTHER)))

    def test_mutant_missing_external_material_matches_is_killed(self):
        module = mutant(("return EXTERNAL_MATERIAL_MISSING\n\n    try:", "return CHECKPOINT_MATCH_CURRENT\n\n    try:"))
        result = module.verify_checkpoint(checkpoint(), None, subject_log_id="audit-main", current_sequence=120, current_head_digest=digest(HEAD))
        self.assertNotEqual(ecp.EXTERNAL_MATERIAL_MISSING, result)

    def test_mutant_promote_provider_timestamp_is_killed(self):
        module = mutant(
            ("\"nonclaims\",\n    }", "\"nonclaims\",\n        \"provider_timestamp\",\n    }"),
            ("if type(subject_log_id) is not str", "if \"provider_timestamp\" in record:\n        return \"CHECKPOINT_MATCH_FRESH\"\n    if type(subject_log_id) is not str"),
        )
        value = checkpoint(provider_timestamp="2026-10-07T00:00:00Z")
        self.assertNotEqual(ecp.INVALID_CHECKPOINT, verify(module, value))

    def test_mutant_multiple_holders_create_quorum_is_killed(self):
        module = mutant(("try:\n        retained = parse_checkpoint_bytes(retained_checkpoint_bytes)", "if type(retained_checkpoint_bytes) is list and len(retained_checkpoint_bytes) > 1:\n        return CHECKPOINT_MATCH_CURRENT\n    try:\n        retained = parse_checkpoint_bytes(retained_checkpoint_bytes)"))
        value = checkpoint()
        retained = [ecp.canonical_checkpoint_bytes(value), ecp.canonical_checkpoint_bytes(checkpoint(holder_id="holder-B"))]
        self.assertNotEqual(ecp.INVALID_CHECKPOINT, verify(module, value, retained=retained))

    def test_mutant_ignore_subject_mismatch_is_killed(self):
        module = mutant(("if record[\"subject_log_id\"] != subject_log_id:", "if False and record[\"subject_log_id\"] != subject_log_id:"))
        self.assertNotEqual(ecp.INVALID_CHECKPOINT, verify(module, subject_log_id="other-log"))


if __name__ == "__main__":
    unittest.main()
