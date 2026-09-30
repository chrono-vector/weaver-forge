"""Attempt state machine, status-last, replay, and recovery tests."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wvma_v1.canonical import digest_excluding_field, sha256_file
from wvma_v1.models import (
    AttemptState,
    AttemptVerdict,
    ResultClass,
    SchemaError,
    build_case_result,
    build_oracle_result,
    build_status,
    strict_parse_case_result,
)
from wvma_v1.state import (
    ReplayError,
    StateError,
    assert_attempt_path_confined,
    compute_attempt_root_digest,
    create_attempt,
    create_recovery_attempt,
    derive_attempt_state,
    finalize_attempt,
    list_published_results,
    publish_case_result,
    recompute_terminal_semantics,
    seal_catalog,
    validate_attempt_id,
    verify_attempt,
    write_exclusive_json,
    write_finalize_intent,
)

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "SYNTHETIC_CATALOG.json"
)

ZERO = "0" * 64
ONE = "1" * 64
TWO = "2" * 64
THREE = "3" * 64
FOUR = "4" * 64


def _oracle(case_id: str, result_class: ResultClass):
    detected = result_class == ResultClass.DETECTED
    return build_oracle_result(
        case_id=case_id,
        mutation_valid=result_class
        not in {ResultClass.INVALID_MUTANT, ResultClass.APPLY_ERROR},
        property_violated=detected or result_class == ResultClass.SURVIVED,
        verifier_exercised=result_class
        not in {ResultClass.APPLY_ERROR, ResultClass.EXECUTION_ERROR},
        expected_rejection_observed=detected,
        result_class=result_class,
        observations=["synthetic"],
        errors=[] if detected else ["blocker"],
    )


def _result(attempt_id: str, catalog_digest: str, case_id: str, cls: ResultClass):
    return build_case_result(
        attempt_id=attempt_id,
        catalog_digest=catalog_digest,
        case_id=case_id,
        property_id="WVMA-S01",
        result_class=cls,
        oracle_result=_oracle(case_id, cls),
        started_at="2026-01-01T00:00:00Z",
        completed_at="2026-01-01T00:00:01Z",
    )


class StateMachineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.catalog = seal_catalog(self.out, FIXTURE)
        self.digest = self.catalog.catalog_digest

    def tearDown(self):
        self.tmp.cleanup()

    def _create(self, attempt_id: str = "WVMA-20260101T000000Z-aaaaaaaa"):
        return create_attempt(
            self.out,
            catalog_digest=self.digest,
            source_revision=ZERO,
            runner_digest=ONE,
            oracle_digest=TWO,
            baseline_receipt_digest=THREE,
            protected_path_inventory_digest=FOUR,
            attempt_id=attempt_id,
        )

    def test_duplicate_attempt_id_rejects(self):
        self._create()
        with self.assertRaises(ReplayError):
            self._create()

    def test_duplicate_case_publication_rejects(self):
        intent = self._create()
        result = _result(
            intent["attempt_id"], self.digest, "WVMA-S01-M01", ResultClass.DETECTED
        )
        publish_case_result(self.out, intent["attempt_id"], result)
        with self.assertRaises(ReplayError):
            publish_case_result(self.out, intent["attempt_id"], result)

    def test_foreign_catalog_case_rejects(self):
        intent = self._create()
        result = _result(
            intent["attempt_id"], self.digest, "WVMA-FOREIGN", ResultClass.DETECTED
        )
        with self.assertRaises(ReplayError):
            publish_case_result(self.out, intent["attempt_id"], result)

    def test_run_in_progress_without_finalize(self):
        intent = self._create()
        self.assertEqual(
            derive_attempt_state(self.out, intent["attempt_id"]),
            AttemptState.RUN_IN_PROGRESS,
        )

    def test_status_without_finalize_intent_is_invalid(self):
        intent = self._create()
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        # Manually write status without finalize intent.
        from wvma_v1.models import build_status

        root_digest = compute_attempt_root_digest(self.out, aid)
        refs = [
            {"case_id": cid, "result_digest": r.result_digest}
            for cid, r in sorted(list_published_results(self.out, aid).items())
        ]
        status = build_status(
            attempt_id=aid,
            catalog_digest=self.digest,
            source_revision=ZERO,
            runner_digest=ONE,
            oracle_digest=TWO,
            state=AttemptState.RUN_COMPLETE,
            verdict=AttemptVerdict.ALL_CRITICAL_DETECTED,
            baseline_receipt_digest=THREE,
            case_result_digests=refs,
            result_counts={"DETECTED": 2},
            blocking_case_ids=[],
            attempt_root_digest=root_digest,
            completed_at="2026-01-01T00:00:02Z",
        )
        write_exclusive_json(
            self.out / "attempts" / aid / "WVMA_STATUS.json", status.to_dict()
        )
        self.assertEqual(
            derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID
        )

    def test_finalize_intent_without_status_is_incomplete(self):
        intent = self._create()
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        root_digest = compute_attempt_root_digest(self.out, aid)
        refs = [
            {"case_id": cid, "result_digest": r.result_digest}
            for cid, r in sorted(list_published_results(self.out, aid).items())
        ]
        write_finalize_intent(
            self.out,
            aid,
            intended_status_digest="a" * 64,
            result_references=refs,
            attempt_root_digest=root_digest,
        )
        self.assertEqual(
            derive_attempt_state(self.out, aid), AttemptState.RUN_INCOMPLETE
        )

    def test_deleted_status_derives_run_incomplete(self):
        intent = self._create()
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        finalize_attempt(self.out, aid)
        self.assertEqual(
            derive_attempt_state(self.out, aid), AttemptState.RUN_COMPLETE
        )
        status_path = self.out / "attempts" / aid / "WVMA_STATUS.json"
        status_path.unlink()
        self.assertEqual(
            derive_attempt_state(self.out, aid), AttemptState.RUN_INCOMPLETE
        )
        self.assertNotEqual(
            derive_attempt_state(self.out, aid), AttemptState.RUN_IN_PROGRESS
        )

    def test_result_digest_mismatch_invalidates(self):
        intent = self._create()
        aid = intent["attempt_id"]
        result = _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED)
        publish_case_result(self.out, aid, result)
        path = (
            self.out
            / "attempts"
            / aid
            / "results"
            / "WVMA-S01-M01"
            / f"{result.result_digest}.json"
        )
        # Corrupt bytes in place by replacing file via temp rename is overwrite;
        # instead delete and write different digest name to simulate mismatch path.
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["completed_at"] = "2099-01-01T00:00:00Z"
        path.unlink()
        # Write mismatched content under the old digest filename using exclusive create.
        write_exclusive_json(path, payload)
        self.assertEqual(
            derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID
        )

    def test_result_deletion_before_finalize_keeps_in_progress_or_incomplete_on_finalize(
        self,
    ):
        intent = self._create()
        aid = intent["attempt_id"]
        r1 = _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED)
        r2 = _result(aid, self.digest, "WVMA-S01-M02", ResultClass.DETECTED)
        publish_case_result(self.out, aid, r1)
        publish_case_result(self.out, aid, r2)
        shutil.rmtree(self.out / "attempts" / aid / "results" / "WVMA-S01-M02")
        status = finalize_attempt(self.out, aid)
        self.assertEqual(status.state, AttemptState.RUN_INCOMPLETE)
        self.assertIsNone(status.verdict)
        self.assertIn("WVMA-S01-M02", status.blocking_case_ids)

    def test_all_critical_detected(self):
        intent = self._create()
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        status = finalize_attempt(self.out, aid)
        self.assertEqual(status.state, AttemptState.RUN_COMPLETE)
        self.assertEqual(status.verdict, AttemptVerdict.ALL_CRITICAL_DETECTED)
        self.assertEqual(verify_attempt(self.out, aid), AttemptState.RUN_COMPLETE)

    def test_critical_non_detected_classes_block_all_critical_detected(self):
        blockers = [
            ResultClass.SURVIVED,
            ResultClass.INVALID_MUTANT,
            ResultClass.APPLY_ERROR,
            ResultClass.EXECUTION_ERROR,
            ResultClass.ORACLE_ERROR,
            ResultClass.MISSING_RESULT,
        ]
        for idx, cls in enumerate(blockers):
            with self.subTest(result_class=cls.value):
                aid = f"WVMA-20260101T000000Z-{idx:08x}"
                self._create(aid)
                publish_case_result(
                    self.out,
                    aid,
                    _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED),
                )
                if cls != ResultClass.MISSING_RESULT:
                    publish_case_result(
                        self.out,
                        aid,
                        _result(aid, self.digest, "WVMA-S01-M02", cls),
                    )
                status = finalize_attempt(self.out, aid)
                if cls == ResultClass.MISSING_RESULT:
                    self.assertEqual(status.state, AttemptState.RUN_INCOMPLETE)
                    self.assertIsNone(status.verdict)
                else:
                    self.assertEqual(status.state, AttemptState.RUN_COMPLETE)
                    self.assertEqual(
                        status.verdict, AttemptVerdict.CRITICAL_SURVIVOR
                    )
                self.assertNotEqual(
                    status.verdict, AttemptVerdict.ALL_CRITICAL_DETECTED
                )

    def test_recovery_creates_new_attempt_prior_byte_identical(self):
        intent = self._create()
        aid = intent["attempt_id"]
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED),
        )
        prior_root = self.out / "attempts" / aid
        before = {
            p.relative_to(prior_root).as_posix(): sha256_file(p)
            for p in sorted(prior_root.rglob("*"))
            if p.is_file()
        }
        prior_attempt_root = compute_attempt_root_digest(self.out, aid)
        recovered = create_recovery_attempt(
            self.out,
            aid,
            attempt_id="WVMA-20260101T010000Z-cccccccc",
        )
        self.assertNotEqual(recovered["attempt_id"], aid)
        self.assertEqual(recovered["prior_attempt_id"], aid)
        self.assertEqual(
            recovered["prior_attempt_root_digest"], prior_attempt_root
        )
        after = {
            p.relative_to(prior_root).as_posix(): sha256_file(p)
            for p in sorted(prior_root.rglob("*"))
            if p.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(
            derive_attempt_state(self.out, recovered["attempt_id"]),
            AttemptState.RUN_IN_PROGRESS,
        )

    def test_attempt_root_excludes_finalize_and_status(self):
        intent = self._create()
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        before = compute_attempt_root_digest(self.out, aid)
        finalize_attempt(self.out, aid)
        after = compute_attempt_root_digest(self.out, aid)
        self.assertEqual(before, after)

    def test_replay_finalize_rejects(self):
        intent = self._create()
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        finalize_attempt(self.out, aid)
        with self.assertRaises(ReplayError):
            finalize_attempt(self.out, aid)


class TerminalSemanticsRemediationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.catalog = seal_catalog(self.out, FIXTURE)
        self.digest = self.catalog.catalog_digest

    def tearDown(self):
        self.tmp.cleanup()

    def _create(self, attempt_id: str = "WVMA-20260101T000000Z-aaaaaaaa"):
        return create_attempt(
            self.out,
            catalog_digest=self.digest,
            source_revision=ZERO,
            runner_digest=ONE,
            oracle_digest=TWO,
            baseline_receipt_digest=THREE,
            protected_path_inventory_digest=FOUR,
            attempt_id=attempt_id,
        )

    def _publish_pair(self, aid: str, second: ResultClass):
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED),
        )
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M02", second),
        )

    def _forge_status(self, aid: str, **overrides):
        root = self.out / "attempts" / aid
        results = list_published_results(self.out, aid)
        refs = [
            {"case_id": cid, "result_digest": r.result_digest}
            for cid, r in sorted(results.items())
        ]
        kwargs = {
            "attempt_id": aid,
            "catalog_digest": self.digest,
            "source_revision": ZERO,
            "runner_digest": ONE,
            "oracle_digest": TWO,
            "state": AttemptState.RUN_COMPLETE,
            "verdict": AttemptVerdict.ALL_CRITICAL_DETECTED,
            "baseline_receipt_digest": THREE,
            "case_result_digests": refs,
            "result_counts": {"DETECTED": 2},
            "blocking_case_ids": [],
            "attempt_root_digest": compute_attempt_root_digest(self.out, aid),
            "completed_at": "2026-01-01T00:00:02Z",
        }
        kwargs.update(overrides)
        status = build_status(**kwargs)
        finalize_path = root / "FINALIZE_INTENT.json"
        status_path = root / "WVMA_STATUS.json"
        if finalize_path.exists():
            finalize_path.unlink()
        if status_path.exists():
            status_path.unlink()
        write_finalize_intent(
            self.out,
            aid,
            intended_status_digest=status.status_digest,
            result_references=refs,
            attempt_root_digest=status.attempt_root_digest,
        )
        write_exclusive_json(status_path, status.to_dict())
        return status

    def test_survived_forged_all_critical_detected_is_invalid(self):
        intent = self._create()
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.SURVIVED)
        real = finalize_attempt(self.out, aid)
        self.assertEqual(real.verdict, AttemptVerdict.CRITICAL_SURVIVOR)
        self._forge_status(aid)
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)
        with self.assertRaises(StateError):
            verify_attempt(self.out, aid)

    def test_forged_result_counts_is_invalid(self):
        intent = self._create("WVMA-20260101T000000Z-bbbbbbbb")
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.DETECTED)
        finalize_attempt(self.out, aid)
        self._forge_status(aid, result_counts={"DETECTED": 99})
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)

    def test_omitted_blocker_is_invalid(self):
        intent = self._create("WVMA-20260101T000000Z-cccccccc")
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.SURVIVED)
        finalize_attempt(self.out, aid)
        self._forge_status(
            aid,
            verdict=AttemptVerdict.CRITICAL_SURVIVOR,
            result_counts={"DETECTED": 1, "SURVIVED": 1},
            blocking_case_ids=[],
        )
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)

    def test_extra_blocker_is_invalid(self):
        intent = self._create("WVMA-20260101T000000Z-dddddddd")
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.DETECTED)
        finalize_attempt(self.out, aid)
        self._forge_status(
            aid,
            verdict=AttemptVerdict.ALL_CRITICAL_DETECTED,
            result_counts={"DETECTED": 2},
            blocking_case_ids=["WVMA-S01-M01"],
        )
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)

    def test_missing_critical_result_incomplete(self):
        intent = self._create("WVMA-20260101T000000Z-eeeeeeee")
        aid = intent["attempt_id"]
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED),
        )
        status = finalize_attempt(self.out, aid)
        self.assertEqual(status.state, AttemptState.RUN_INCOMPLETE)
        self.assertIsNone(status.verdict)
        self.assertIn("WVMA-S01-M02", status.blocking_case_ids)
        self.assertEqual(status.result_counts.get("MISSING_RESULT"), 1)
        semantics = recompute_terminal_semantics(
            self.catalog, list_published_results(self.out, aid)
        )
        self.assertEqual(semantics.state, AttemptState.RUN_INCOMPLETE)

    def test_foreign_result_invalid(self):
        intent = self._create("WVMA-20260101T000000Z-ffffffff")
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.DETECTED)
        foreign = _result(aid, self.digest, "WVMA-FOREIGN", ResultClass.DETECTED)
        # Force foreign case onto disk after catalog-bound publishes.
        case_dir = self.out / "attempts" / aid / "results" / foreign.case_id
        case_dir.mkdir(parents=False, exist_ok=False)
        write_exclusive_json(case_dir / f"{foreign.result_digest}.json", foreign.to_dict())
        status = finalize_attempt(self.out, aid)
        self.assertEqual(status.state, AttemptState.RUN_INVALID)
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)

    def test_valid_recomputed_status(self):
        intent = self._create("WVMA-20260101T000001Z-aaaaaaaa")
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.DETECTED)
        status = finalize_attempt(self.out, aid)
        semantics = recompute_terminal_semantics(
            self.catalog, list_published_results(self.out, aid)
        )
        self.assertEqual(semantics.state, AttemptState.RUN_COMPLETE)
        self.assertEqual(semantics.verdict, AttemptVerdict.ALL_CRITICAL_DETECTED)
        self.assertEqual(status.verdict, semantics.verdict)
        self.assertEqual(dict(status.result_counts), dict(semantics.result_counts))
        self.assertEqual(
            list(status.blocking_case_ids), list(semantics.blocking_case_ids)
        )
        self.assertEqual(verify_attempt(self.out, aid), AttemptState.RUN_COMPLETE)

    def test_stored_recomputed_semantic_mismatch_invalid(self):
        intent = self._create("WVMA-20260101T000002Z-aaaaaaaa")
        aid = intent["attempt_id"]
        self._publish_pair(aid, ResultClass.SURVIVED)
        finalize_attempt(self.out, aid)
        self._forge_status(
            aid,
            verdict=AttemptVerdict.ALL_CRITICAL_DETECTED,
            result_counts={"DETECTED": 2},
            blocking_case_ids=[],
        )
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)


class AttemptIdConfinementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.catalog = seal_catalog(self.out, FIXTURE)
        self.digest = self.catalog.catalog_digest

    def tearDown(self):
        self.tmp.cleanup()

    def _try_create(self, attempt_id: str):
        return create_attempt(
            self.out,
            catalog_digest=self.digest,
            source_revision=ZERO,
            runner_digest=ONE,
            oracle_digest=TWO,
            baseline_receipt_digest=THREE,
            protected_path_inventory_digest=FOUR,
            attempt_id=attempt_id,
        )

    def test_path_traversal_forms_rejected(self):
        bad_ids = [
            "../",
            "..\\",
            "WVMA-20260101T000000Z-aaaaaaaa/nested",
            "WVMA-20260101T000000Z-aaaaaaaa\\nested",
            "/absolute/path",
            "C:WVMA-20260101T000000Z-aaaaaaaa",
            "\\\\server\\share\\WVMA",
            "WVMA-/../../../escaped-out-root",
        ]
        for bad in bad_ids:
            with self.subTest(attempt_id=bad):
                with self.assertRaises(StateError):
                    validate_attempt_id(bad)
                with self.assertRaises(StateError):
                    self._try_create(bad)

    def test_invalid_timestamp_rejects(self):
        bad = "WVMA-20261301T000000Z-aaaaaaaa"
        with self.assertRaises(StateError):
            validate_attempt_id(bad)

    def test_unicode_digit_substitution_rejects(self):
        # Fullwidth digit in timestamp must not pass ASCII grammar.
        bad = "WVMA-20260101T00000０Z-aaaaaaaa"
        with self.assertRaises(StateError):
            validate_attempt_id(bad)

    def test_uppercase_nonce_rejects(self):
        bad = "WVMA-20260101T000000Z-DEADBEEF"
        with self.assertRaises(StateError):
            validate_attempt_id(bad)

    def test_valid_attempt_id_and_direct_child_confinement(self):
        aid = "WVMA-20260101T000000Z-aaaaaaaa"
        self.assertEqual(validate_attempt_id(aid), aid)
        path = assert_attempt_path_confined(self.out, aid)
        self.assertEqual(path.parent, (self.out / "attempts").resolve())
        self.assertEqual(path.name, aid)
        intent = self._try_create(aid)
        self.assertEqual(intent["attempt_id"], aid)

    def test_no_directory_created_for_invalid_id(self):
        bad = "WVMA-/../../../escaped-out-root"
        attempts = self.out / "attempts"
        before = set(attempts.rglob("*")) if attempts.exists() else set()
        with self.assertRaises(StateError):
            self._try_create(bad)
        after = set(attempts.rglob("*")) if attempts.exists() else set()
        self.assertEqual(before, after)
        self.assertFalse((self.out / "escaped-out-root").exists())
        self.assertFalse(any("escaped-out-root" in str(p) for p in self.out.rglob("*")))


class DirectAdversarialRetests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.catalog = seal_catalog(self.out, FIXTURE)
        self.digest = self.catalog.catalog_digest

    def tearDown(self):
        self.tmp.cleanup()

    def _create(self, attempt_id: str = "WVMA-20260101T000000Z-aaaaaaaa"):
        return create_attempt(
            self.out,
            catalog_digest=self.digest,
            source_revision=ZERO,
            runner_digest=ONE,
            oracle_digest=TWO,
            baseline_receipt_digest=THREE,
            protected_path_inventory_digest=FOUR,
            attempt_id=attempt_id,
        )

    def test_attack1_false_detected_all_proofs_false(self):
        oracle = build_oracle_result(
            case_id="WVMA-S01-M01",
            mutation_valid=True,
            property_violated=True,
            verifier_exercised=True,
            expected_rejection_observed=True,
            result_class=ResultClass.DETECTED,
        )
        body = {
            "schema_version": "wvma_v1.result.v1",
            "authority": False,
            "attempt_id": "WVMA-20260101T000000Z-aaaaaaaa",
            "catalog_digest": self.digest,
            "case_id": "WVMA-S01-M01",
            "property_id": "WVMA-S01",
            "result_class": "DETECTED",
            "mutation_proof": {"applied": False},
            "violation_proof": {"observed": False},
            "verifier_exercise_proof": {"invoked": False},
            "process_observation": {"exit_code": 0},
            "filesystem_observations": [],
            "digest_observations": [],
            "oracle_result": oracle.to_dict(),
            "started_at": "2026-01-01T00:00:00Z",
            "completed_at": "2026-01-01T00:00:01Z",
        }
        body["result_digest"] = digest_excluding_field(body, "result_digest")
        with self.assertRaises(SchemaError):
            strict_parse_case_result(body)
        intent = self._create()
        aid = intent["attempt_id"]
        with self.assertRaises(SchemaError):
            publish_case_result(self.out, aid, body)
        # Cannot reach ALL_CRITICAL_DETECTED via false DETECTED proofs.
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M01", ResultClass.SURVIVED),
        )
        status = finalize_attempt(self.out, aid)
        self.assertNotEqual(status.verdict, AttemptVerdict.ALL_CRITICAL_DETECTED)

    def test_attack2_rebound_all_critical_detected_over_survived(self):
        intent = self._create("WVMA-20260101T000000Z-bbbbbbbb")
        aid = intent["attempt_id"]
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M01", ResultClass.DETECTED),
        )
        publish_case_result(
            self.out,
            aid,
            _result(aid, self.digest, "WVMA-S01-M02", ResultClass.SURVIVED),
        )
        real = finalize_attempt(self.out, aid)
        self.assertEqual(real.verdict, AttemptVerdict.CRITICAL_SURVIVOR)
        results = list_published_results(self.out, aid)
        refs = [
            {"case_id": cid, "result_digest": r.result_digest}
            for cid, r in sorted(results.items())
        ]
        forged = build_status(
            attempt_id=aid,
            catalog_digest=self.digest,
            source_revision=ZERO,
            runner_digest=ONE,
            oracle_digest=TWO,
            state=AttemptState.RUN_COMPLETE,
            verdict=AttemptVerdict.ALL_CRITICAL_DETECTED,
            baseline_receipt_digest=THREE,
            case_result_digests=refs,
            result_counts={"DETECTED": 2},
            blocking_case_ids=[],
            attempt_root_digest=compute_attempt_root_digest(self.out, aid),
            completed_at="2026-01-01T00:00:02Z",
        )
        root = self.out / "attempts" / aid
        (root / "FINALIZE_INTENT.json").unlink()
        (root / "WVMA_STATUS.json").unlink()
        write_finalize_intent(
            self.out,
            aid,
            intended_status_digest=forged.status_digest,
            result_references=refs,
            attempt_root_digest=forged.attempt_root_digest,
        )
        write_exclusive_json(root / "WVMA_STATUS.json", forged.to_dict())
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)
        with self.assertRaises(StateError):
            verify_attempt(self.out, aid)

    def test_attack3_malformed_finalize_intent(self):
        intent = self._create("WVMA-20260101T000000Z-cccccccc")
        aid = intent["attempt_id"]
        for case_id in self.catalog.critical_case_ids:
            publish_case_result(
                self.out,
                aid,
                _result(aid, self.digest, case_id, ResultClass.DETECTED),
            )
        finalize_attempt(self.out, aid)
        finalize_path = self.out / "attempts" / aid / "FINALIZE_INTENT.json"
        malformed = {
            "schema_version": "wvma_v1.finalize_intent.v1",
            "authority": True,
            "attempt_id": "WVMA-20260101T000000Z-ffffffff",
            "attempt_root_digest": "a" * 64,
            "intended_status_digest": "b" * 64,
            "result_references": [],
            "unknown_field": True,
        }
        finalize_path.unlink()
        # Bypass writer to plant adversarial finalize bytes.
        finalize_path.write_text(json.dumps(malformed), encoding="utf-8")
        self.assertEqual(derive_attempt_state(self.out, aid), AttemptState.RUN_INVALID)
        with self.assertRaises(StateError):
            verify_attempt(self.out, aid)

    def test_attack4_escaped_attempt_id_rejected_before_mkdir(self):
        bad = "WVMA-/../../../escaped-out-root"
        with self.assertRaises(StateError):
            create_attempt(
                self.out,
                catalog_digest=self.digest,
                source_revision=ZERO,
                runner_digest=ONE,
                oracle_digest=TWO,
                baseline_receipt_digest=THREE,
                protected_path_inventory_digest=FOUR,
                attempt_id=bad,
            )
        self.assertFalse((self.out / "escaped-out-root").exists())
        attempts = self.out / "attempts"
        if attempts.exists():
            self.assertFalse(any(bad in str(p) for p in attempts.rglob("*")))


if __name__ == "__main__":
    unittest.main()

