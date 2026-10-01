"""B1 artifact mutation catalog tests for WVMA-V1."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from wvma_v1.artifact_cases import (
    CASE_DEFS,
    CATALOG_PATH,
    CRITICAL_CASE_IDS,
    apply_case_mutation,
    build_catalog_document,
    case_by_id,
    load_committed_catalog,
    write_catalog,
)
from wvma_v1.baselines import (
    FIXED_CAMPAIGN_INVOCATION_ID,
    FIXED_UTC,
    PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
    PROFILE_AUDIT_R4B_REVIEW_CHAIN,
    PROFILE_AUDIT_R4B_ZERO_REVIEW,
    PROFILE_CAMPAIGN_TEST_ONLY,
    STABLE_ROOT,
    build_audit_human_review_prefreeze,
    build_audit_r4b_review_chain,
    build_audit_r4b_zero_review,
    build_campaign_test_only,
    rebind_freeze_package_hashes,
)
from wvma_v1.canonical import digest_excluding_field
from wvma_v1.models import ResultClass, strict_parse_catalog
from wvma_v1.mutations import apply_mutation
from wvma_v1.oracle import CaseEvaluationInput, evaluate_case
from wvma_v1.runner import InvocationContract, run_baseline, run_mutation_case
from wvma_v1.workspace import create_disposable_root

ACTIVE_REPO = Path(__file__).resolve().parents[2]
_COMMITTED_CATALOG_BYTES: bytes | None = None
_DUMMY_PREIMAGE = "11" * 32
_DUMMY_POSTIMAGE = "22" * 32


def setUpModule() -> None:
    global _COMMITTED_CATALOG_BYTES
    if not CATALOG_PATH.is_file():
        raise AssertionError(f"committed catalog missing: {CATALOG_PATH}")
    _COMMITTED_CATALOG_BYTES = CATALOG_PATH.read_bytes()


def tearDownModule() -> None:
    if _COMMITTED_CATALOG_BYTES is None:
        return
    current = CATALOG_PATH.read_bytes()
    if current != _COMMITTED_CATALOG_BYTES:
        raise AssertionError("tests rewrote WVMA_V1_CATALOG.json")


def _inventory_protected(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            out[rel] = digest
    return out


def _write_markers(workspace: Path, target: Path, case_id: str) -> None:
    if case_id.startswith("C10"):
        aurora = target
        while aurora.name != "aurora_audit" and aurora != aurora.parent:
            aurora = aurora.parent
        marker = {
            "workspace": aurora.relative_to(workspace).as_posix(),
            "campaign_id": target.name,
        }
        (workspace / ".wvma_campaign").write_text(
            json.dumps(marker, sort_keys=True), encoding="utf-8"
        )
    else:
        (workspace / ".wvma_audit_root").write_text(
            target.relative_to(workspace).as_posix(), encoding="utf-8"
        )


def _build_baseline(case_id: str, workspace: Path) -> Path:
    case = case_by_id(case_id)
    if case.baseline_profile == PROFILE_AUDIT_R4B_ZERO_REVIEW:
        force_fail = case_id == "C01-01"
        freeze = case_id != "C01-01"
        # C01-01 needs decision-stage FAIL package (no freeze required for semantics).
        if case_id == "C01-01":
            return build_audit_r4b_zero_review(
                workspace,
                audit_id="WFA-WVMA-B1-ZERO",
                force_fail=True,
                freeze=False,
            )
        return build_audit_r4b_zero_review(
            workspace,
            audit_id="WFA-WVMA-B1-ZERO",
            force_fail=False,
            freeze=True,
        )
    if case.baseline_profile == PROFILE_AUDIT_R4B_REVIEW_CHAIN:
        return build_audit_r4b_review_chain(
            workspace, audit_id="WFA-WVMA-B1-CHAIN"
        )
    if case.baseline_profile == PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE:
        root, _req = build_audit_human_review_prefreeze(
            workspace, audit_id="WFA-WVMA-B1-HR", with_accepted_review=True
        )
        return root
    if case.baseline_profile == PROFILE_CAMPAIGN_TEST_ONLY:
        return build_campaign_test_only(
            workspace, campaign_id=f"wvma_b1_{case_id.replace('-', '_').lower()}"
        )
    raise AssertionError(case.baseline_profile)


def _baseline_invocation(case_id: str) -> str:
    case = case_by_id(case_id)
    if case.verifier_invocation_id == "audit.freeze_run":
        # Prefreeze baseline: semantics/gate path is deferred; use a no-op
        # acceptance check via verify_semantics (deferred until freeze).
        return "audit.verify_semantics"
    return case.verifier_invocation_id


def _prepare_c10_expect(workspace: Path, case_id: str, campaign_dir: Path) -> None:
    state_path = campaign_dir / "CAMPAIGN_STATE.json"
    if not state_path.is_file():
        return
    data = json.loads(state_path.read_text(encoding="utf-8"))
    claims = data.get("claims") or {}
    if case_id == "C10-01":
        cid = next(
            (c for c, r in claims.items() if r.get("state") != "PASS"),
            next(iter(claims)),
        )
        payload = {"mode": "false_pass", "claim_id": cid}
    elif case_id == "C10-02":
        cid = next(
            (c for c, r in claims.items() if r.get("state") == "PASS"),
            next(iter(claims)),
        )
        payload = {"mode": "reuse_fail", "claim_id": cid}
    else:
        payload = {
            "mode": "foreign",
            "claim_id": "FOREIGN-CLAIM-NO-BINDING",
        }
    (workspace / ".wvma_c10_expect").write_text(
        json.dumps(payload, sort_keys=True), encoding="utf-8"
    )


def _assert_final_target_content(case_id: str, final_path: Path) -> None:
    """Sealed postimage is the final same-file state the oracle observes."""
    if case_id not in {"C01-01", "C01-02", "C10-01"}:
        return
    data = json.loads(final_path.read_text(encoding="utf-8"))
    if case_id == "C01-01":
        assert data["decision"] == "PASS"
        assert data["claim_result"] == "PASS"
        assert data["reason"] == "WVMA_FALSE_PASS"
        return
    if case_id == "C01-02":
        decision = data["decision"]
        assert decision["promoted_to_full"] is True
        assert decision["broader_classification"] == "CRYPTO_SUPPORTED_E2E_FULL"
        return
    claims = data.get("claims") or {}
    matched = [
        row
        for row in claims.values()
        if isinstance(row, dict)
        and row.get("state") == "PASS"
        and row.get("reason") == "WVMA_FALSE_PASS"
    ]
    assert matched, "C10-01 final claim state was not sealed"
    integrity = data.get("state_integrity") or {}
    assert isinstance(integrity.get("digest"), str) and len(integrity["digest"]) == 64


def _measure_case(case_id: str) -> dict[str, object]:
    case = case_by_id(case_id)
    with tempfile.TemporaryDirectory(prefix="wvma-b1-det-") as td:
        workspace = create_disposable_root(
            parent=Path(td),
            prefix="ws-",
            active_repository=ACTIVE_REPO,
        )
        target = _build_baseline(case_id, workspace)
        app, spec, rel = apply_case_mutation(workspace, case, target)
        final_path = workspace / Path(*rel.split("/"))
        body = final_path.read_bytes() if final_path.is_file() else b""
        info: dict[str, object] = {
            "pre": app.preimage_sha256,
            "post": app.postimage_sha256,
            "body": body,
            "workspace": str(workspace.resolve()),
            "spec": spec,
        }
        if case_id == "C07-04":
            residue = (
                target / "freeze" / ".wf_freeze_tmp_WFA-WVMA-B1-ZERO_deadbeef"
            )
            info["residue"] = residue.is_dir()
        return info


def _run_case(case_id: str) -> ResultClass:
    case = case_by_id(case_id)
    with tempfile.TemporaryDirectory(prefix="wvma-b1-") as td:
        parent = Path(td)
        workspace = create_disposable_root(
            parent=parent,
            prefix="ws-",
            active_repository=ACTIVE_REPO,
        )
        before = _inventory_protected(ACTIVE_REPO / "wvma_v1")
        target = _build_baseline(case_id, workspace)
        _write_markers(workspace, target, case_id)

        base_id = _baseline_invocation(case_id)
        baseline_receipt = run_baseline(
            workspace_root=workspace,
            contract=InvocationContract(invocation_id=base_id),
            active_repository=ACTIVE_REPO,
        )
        if case_id.startswith("C08-0") and case_id in {"C08-01", "C08-02", "C08-03"}:
            # Prefreeze: baseline semantics deferred-ok; require review present.
            assert (target / "HUMAN_REVIEW.json").is_file()
            assert baseline_receipt.verify_ok_claimed is True
        elif case.expect_invalid_mutant:
            # Will freeze inside apply; baseline pre-freeze semantics ok.
            assert baseline_receipt.exit_code == 0
        else:
            assert baseline_receipt.verify_ok_claimed is True, (
                case_id,
                baseline_receipt.stdout_text_preview,
            )

        app, spec, target_rel = apply_case_mutation(workspace, case, target)
        sealed = load_committed_catalog().mutation_by_case_id(case_id)
        assert spec == sealed
        assert target_rel == sealed.target_relative_path
        assert app.applied is True
        assert app.preimage_sha256 == sealed.expected_preimage_sha256
        assert app.postimage_sha256 == sealed.expected_postimage_sha256
        assert sealed.operation_enum == spec.operation_enum
        assert spec.operation_arguments == sealed.operation_arguments
        final_path = workspace / Path(*sealed.target_relative_path.split("/"))
        if sealed.operation_enum == "DELETE_DECLARED_FILE":
            assert not final_path.exists()
        else:
            assert hashlib.sha256(final_path.read_bytes()).hexdigest() == (
                sealed.expected_postimage_sha256
            )
        _assert_final_target_content(case_id, final_path)
        assert app.preimage_sha256 != app.postimage_sha256 or case.operation_enum == "DELETE_DECLARED_FILE"
        if case.operation_enum != "DELETE_DECLARED_FILE":
            assert app.preimage_sha256 != app.postimage_sha256

        if case_id.startswith("C10"):
            _prepare_c10_expect(workspace, case_id, target)

        mut_receipt = run_mutation_case(
            workspace_root=workspace,
            contract=InvocationContract(invocation_id=case.verifier_invocation_id),
            active_repository=ACTIVE_REPO,
            require_target_relative_path=spec.target_relative_path
            if case.operation_enum != "DELETE_DECLARED_FILE"
            else None,
        )

        # Independent observations (do not trust self_claimed_result alone).
        property_violated = None
        rejection = None
        if case.expect_invalid_mutant:
            property_violated = False
            rejection = False
        oracle = evaluate_case(
            CaseEvaluationInput(
                case_id=case_id,
                mutation=app,
                expected_preimage_sha256=spec.expected_preimage_sha256,
                expected_postimage_sha256=spec.expected_postimage_sha256,
                baseline_receipt=baseline_receipt,
                mutation_receipt=mut_receipt,
                property_violated=property_violated,
                expected_rejection_observed=rejection,
            )
        )
        after = _inventory_protected(ACTIVE_REPO / "wvma_v1")
        assert before == after, "active wvma_v1 tree mutated"
        return oracle.result_class


class TestArtifactCatalogStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The committed catalog is the mutation authority. Tests must not write it.
        cls.catalog = load_committed_catalog()

    def test_catalog_parses_and_authority_false(self):
        self.assertFalse(self.catalog.authority)
        self.assertEqual(self.catalog.catalog_id, "WVMA-V1-ARTIFACT-B1")

    def test_no_missing_critical_cases(self):
        sealed = set(self.catalog.critical_case_ids)
        self.assertEqual(sealed, set(CRITICAL_CASE_IDS))

    def test_no_duplicate_critical_cases(self):
        ids = list(self.catalog.critical_case_ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_executable_commands_in_catalog(self):
        raw = CATALOG_PATH.read_text(encoding="utf-8").lower()
        for banned in ("rm -rf", "subprocess", "os.system", "powershell", "cmd.exe"):
            self.assertNotIn(banned, raw)

    def test_case_ids_unique(self):
        ids = [c.case_id for c in CASE_DEFS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_placeholder_paths_or_dummy_digests(self):
        raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        mutations = raw["mutations"]
        self.assertEqual(len(mutations), 30)
        pres = [row["expected_preimage_sha256"] for row in mutations]
        posts = [row["expected_postimage_sha256"] for row in mutations]
        self.assertGreater(len(set(pres)), 1)
        self.assertGreater(len(set(posts)), 1)
        for row in mutations:
            path = row["target_relative_path"]
            self.assertFalse(path.startswith("placeholder/"), row["case_id"])
            self.assertNotIn("placeholder", path)
            self.assertNotEqual(row["expected_preimage_sha256"], _DUMMY_PREIMAGE)
            self.assertNotEqual(row["expected_postimage_sha256"], _DUMMY_POSTIMAGE)
            self.assertEqual(len(row["expected_preimage_sha256"]), 64)
            self.assertEqual(len(row["expected_postimage_sha256"]), 64)
            sealed = self.catalog.mutation_by_case_id(row["case_id"])
            self.assertEqual(sealed.target_relative_path, path)
            self.assertEqual(sealed.operation_enum, row["operation_enum"])
            self.assertEqual(sealed.operation_arguments, row["operation_arguments"])

    def test_builder_does_not_rewrite_committed_catalog(self):
        before = CATALOG_PATH.read_bytes()
        doc = build_catalog_document()
        self.assertEqual(CATALOG_PATH.read_bytes(), before)
        self.assertEqual(doc["catalog_digest"], json.loads(before)["catalog_digest"])
        self.assertFalse(doc["authority"])


class TestArtifactCases(unittest.TestCase):
    def _assert_detected(self, case_id: str):
        result = _run_case(case_id)
        self.assertEqual(result, ResultClass.DETECTED, case_id)

    def test_C01_01(self):
        self._assert_detected("C01-01")

    def test_C01_02(self):
        self._assert_detected("C01-02")

    def test_C02_01(self):
        self._assert_detected("C02-01")

    def test_C02_02(self):
        self._assert_detected("C02-02")

    def test_C03_01(self):
        self._assert_detected("C03-01")

    def test_C04_01(self):
        self._assert_detected("C04-01")

    def test_C04_02(self):
        self._assert_detected("C04-02")

    def test_C04_03(self):
        self._assert_detected("C04-03")

    def test_C04_04(self):
        self._assert_detected("C04-04")

    def test_C05_01(self):
        self._assert_detected("C05-01")

    def test_C05_02(self):
        self._assert_detected("C05-02")

    def test_C05_03(self):
        self._assert_detected("C05-03")

    def test_C06_01(self):
        self._assert_detected("C06-01")

    def test_C06_02(self):
        self._assert_detected("C06-02")

    def test_C06_03(self):
        self._assert_detected("C06-03")

    def test_C07_01(self):
        self._assert_detected("C07-01")

    def test_C07_02(self):
        self._assert_detected("C07-02")

    def test_C07_03(self):
        self._assert_detected("C07-03")

    def test_C07_04(self):
        self._assert_detected("C07-04")

    def test_C08_01(self):
        self._assert_detected("C08-01")

    def test_C08_02(self):
        self._assert_detected("C08-02")

    def test_C08_03(self):
        self._assert_detected("C08-03")

    def test_C08_04(self):
        self._assert_detected("C08-04")

    def test_C08_05(self):
        self._assert_detected("C08-05")

    def test_C08_unbound_metadata_invalid_mutant(self):
        result = _run_case("C08-UM-01")
        self.assertEqual(result, ResultClass.INVALID_MUTANT)

    def test_C09_01(self):
        self._assert_detected("C09-01")

    def test_C09_02(self):
        self._assert_detected("C09-02")

    def test_C10_01(self):
        self._assert_detected("C10-01")

    def test_C10_02(self):
        self._assert_detected("C10-02")

    def test_C10_03(self):
        self._assert_detected("C10-03")


class TestArtifactAdversarialGuards(unittest.TestCase):
    def test_fake_detected_label_rejected(self):
        """Self-claimed DETECTED without rejection signal is not accepted."""
        with tempfile.TemporaryDirectory(prefix="wvma-b1-fake-") as td:
            parent = Path(td)
            workspace = create_disposable_root(
                parent=parent,
                prefix="ws-",
                active_repository=ACTIVE_REPO,
            )
            syn = workspace / "synthetic"
            syn.mkdir()
            from wvma_v1.canonical import canonical_bytes

            (syn / "artifact.json").write_bytes(
                canonical_bytes({"status": "accepted", "n": 1})
            )
            # Canary reports DETECTED while verify_ok True.
            receipt = run_baseline(
                workspace_root=workspace,
                contract=InvocationContract(invocation_id="synthetic.canary_pass"),
            )
            self.assertEqual(receipt.self_claimed_result, "DETECTED")
            self.assertTrue(receipt.verify_ok_claimed)
            from wvma_v1.mutations import MutationApplication

            fake_mut = MutationApplication(
                case_id="FAKE",
                operation_enum="SET_JSON_POINTER",
                target_relative_path="synthetic/artifact.json",
                preimage_sha256="11" * 32,
                postimage_sha256="22" * 32,
                applied=True,
            )
            oracle = evaluate_case(
                CaseEvaluationInput(
                    case_id="FAKE",
                    mutation=fake_mut,
                    expected_preimage_sha256="11" * 32,
                    expected_postimage_sha256="22" * 32,
                    baseline_receipt=receipt,
                    mutation_receipt=receipt,
                )
            )
            self.assertNotEqual(oracle.result_class, ResultClass.DETECTED)

    def test_deterministic_repeat_C03_01(self):
        a = _run_case("C03-01")
        b = _run_case("C03-01")
        self.assertEqual(a, ResultClass.DETECTED)
        self.assertEqual(a, b)

    def test_active_repository_unchanged_after_case(self):
        before = _inventory_protected(ACTIVE_REPO / "docs")
        _run_case("C05-01")
        after = _inventory_protected(ACTIVE_REPO / "docs")
        self.assertEqual(before, after)


class TestDeterministicFinalArtifacts(unittest.TestCase):
    def test_c07_04_deterministic_across_roots(self):
        first = _measure_case("C07-04")
        second = _measure_case("C07-04")
        sealed = load_committed_catalog().mutation_by_case_id("C07-04")
        self.assertEqual(first["pre"], second["pre"])
        self.assertEqual(first["post"], second["post"])
        self.assertEqual(first["body"], second["body"])
        self.assertEqual(first["pre"], sealed.expected_preimage_sha256)
        self.assertEqual(first["post"], sealed.expected_postimage_sha256)
        self.assertEqual(sealed.operation_arguments["pointer"], "/state")
        self.assertEqual(sealed.operation_arguments["value"], "FREEZE_IN_PROGRESS")
        status = json.loads(first["body"])
        self.assertEqual(status["state"], "FREEZE_IN_PROGRESS")
        freeze_directory = status["freeze_directory"]
        sha_path = status["sha256sums"]
        self.assertTrue(freeze_directory.startswith(f"{STABLE_ROOT}/"))
        self.assertTrue(sha_path.startswith(f"{STABLE_ROOT}/"))
        self.assertNotIn(":", freeze_directory)
        self.assertNotIn(":", sha_path)
        workspace = str(first["workspace"])
        self.assertNotIn(workspace, freeze_directory)
        self.assertNotIn(workspace, sha_path)
        self.assertNotIn(workspace, first["body"].decode("utf-8"))
        self.assertTrue(first["residue"])
        self.assertTrue(second["residue"])

    def test_c10_02_deterministic_across_roots(self):
        first = _measure_case("C10-02")
        second = _measure_case("C10-02")
        sealed = load_committed_catalog().mutation_by_case_id("C10-02")
        self.assertEqual(first["pre"], second["pre"])
        self.assertEqual(first["post"], second["post"])
        self.assertEqual(first["body"], second["body"])
        self.assertEqual(first["pre"], sealed.expected_preimage_sha256)
        self.assertEqual(first["post"], sealed.expected_postimage_sha256)
        self.assertEqual(
            sealed.operation_arguments["value"], "reuse:WRONG_AUDIT_ID_WVMA"
        )
        state = json.loads(first["body"])
        self.assertEqual(state["workspace"], "aurora_audit")
        self.assertEqual(state["invocation_id"], FIXED_CAMPAIGN_INVOCATION_ID)
        self.assertEqual(state["updated_at_utc"], FIXED_UTC)
        claims = state["claims"]
        self.assertEqual(
            claims["AUR-A-001"]["evidence_id"], "reuse:WRONG_AUDIT_ID_WVMA"
        )
        for row in claims.values():
            if "validated_at_utc" in row:
                self.assertEqual(row["validated_at_utc"], FIXED_UTC)
            if "updated_at_utc" in row:
                self.assertEqual(row["updated_at_utc"], FIXED_UTC)
        text = first["body"].decode("utf-8")
        self.assertNotIn(str(first["workspace"]), text)
        self.assertNotIn(str(second["workspace"]), second["body"].decode("utf-8"))


class TestCatalogSealDigest(unittest.TestCase):
    def test_write_catalog_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "WVMA_V1_CATALOG.json"
            doc = write_catalog(path, build_catalog_document())
            parsed = strict_parse_catalog(doc)
            self.assertEqual(parsed.catalog_digest, doc["catalog_digest"])
            again = digest_excluding_field(doc, "catalog_digest")
            self.assertEqual(again, doc["catalog_digest"])


if __name__ == "__main__":
    unittest.main()
