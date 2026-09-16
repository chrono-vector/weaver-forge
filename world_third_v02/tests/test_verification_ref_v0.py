"""Tests for WORLD THIRD v0.2 Weaver VERIFICATION_REF (additive)."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from world_third_v02.verification_ref_v0 import (  # noqa: E402
    ARTIFACT_TYPE,
    ARTIFACT_TYPE_EIG_CLEANUP_RESULT,
    ARTIFACT_TYPE_GENERIC_VERDICT,
    ARTIFACT_TYPE_LIFECYCLE_DECISION,
    SCHEMA_VERSION,
    WorldThirdVerificationRefError,
    build_verification_ref_v0,
    compute_verification_digest_v0,
    resolve_verification_ref_v0,
    validate_verification_ref_v0,
    write_verification_artifact_bytes,
)

COMMIT_A = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
COMMIT_B = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _eig_pass_result() -> dict:
    return {
        "verdict": "PASS",
        "read_only": True,
        "mutation_attempted": False,
        "delete_authority": False,
        "claims_independent_verification": False,
        "claims_iw_acceptance": False,
        "raw_secret_scan_pass": True,
        "details": {
            "schema_version": "eig-cleanup-residue-verifier-v0",
            "residue_status": "CLEARED",
            "self_check_ne_independent_verification": True,
            "weaver_verify_ne_iw_acceptance": True,
            "adapter_success_ne_cleared": True,
        },
        "nonclaims": {
            "self_check_ne_independent_verification": True,
            "weaver_verify_ne_iw_acceptance": True,
        },
    }


def _lifecycle_decision(
    *,
    decision: str = "PASS",
    claim_id: str = "P5-PRIMARY",
    commit: str | None = COMMIT_A,
    target_identity: str | None = "repo:fixture-target",
) -> dict:
    out = {
        "decision": decision,
        "claim_result": decision,
        "claim_id": claim_id,
        "reason": "TEST_FIXTURE",
        "promoted": False,
        "promoted_to_full": False,
        "vectors": {"POSITIVE_DIGEST_MATCH": decision},
    }
    if commit is not None:
        out["target_commit"] = commit
    if target_identity is not None:
        out["target_identity"] = target_identity
    return out


def _generic_verdict(
    *,
    verdict: str,
    target_identity: str = "obj:sandbox/fixture-1",
    commit: str = COMMIT_A,
    claim_id: str = "CLAIM-1",
    run_id: str = "WFA-TEST-001",
) -> dict:
    return {
        "verdict": verdict,
        "claims_iw_acceptance": False,
        "target_identity": target_identity,
        "target_commit_or_version": {"binding_kind": "git_commit", "value": commit},
        "scope": {"kind": "claim", "claim_id": claim_id},
        "claim_id": claim_id,
        "run_id": run_id,
        "created_at": "2026-09-16T00:00:00Z",
        "nonclaims": {
            "self_check_ne_independent_verification": True,
            "weaver_verify_ne_iw_acceptance": True,
        },
    }


class TestWorldThirdWeaverVerificationRefV0(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="wtvr-v0-"))
        self.artifact_root = self.tmp / "artifacts"
        self.ref_root = self.tmp / "refs"
        self.artifact_root.mkdir(parents=True)
        self.ref_root.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_artifact(self, relative: str, obj: dict) -> tuple[str, int]:
        path = self.artifact_root / relative
        return write_verification_artifact_bytes(path, obj)

    def _build_from_generic(
        self,
        *,
        relative: str = "results/verdict.json",
        work_id: str = "work-wtvr-001",
        verdict: str = "PASS",
        artifact: dict | None = None,
        **kwargs,
    ) -> dict:
        art = artifact if artifact is not None else _generic_verdict(verdict=verdict)
        sha, nbytes = self._write_artifact(relative, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        params = {
            "work_id": work_id,
            "verifier": "weaver-forge",
            "verification_artifact_ref": {
                "artifact_ref": relative,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": sha,
                "bytes_length": nbytes,
                "created_at": "2026-09-16T00:00:00Z",
            },
            "verification_type": "weaver_verification_verdict_v0",
            "verification_result": art["verdict"],
            "created_at": "2026-09-16T01:00:00Z",
            "verification_digest": digest,
            "target_identity": art.get("target_identity"),
            "target_commit_or_version": art.get("target_commit_or_version"),
            "underlying_scope": art.get("scope"),
            "underlying_claim_id": art.get("claim_id"),
            "underlying_run_id": art.get("run_id"),
            "underlying_nonclaims": art.get("nonclaims"),
            "claims_iw_acceptance": False,
        }
        params.update(kwargs)
        # Drop Nones that build treats as omitted when not passed — rebuild cleanly.
        clean = {k: v for k, v in params.items() if v is not None}
        return build_verification_ref_v0(**clean)

    # 1
    def test_valid_existing_weaver_artifact_produces_valid_ref(self) -> None:
        ref = self._build_from_generic()
        self.assertEqual(ref["artifact_type"], ARTIFACT_TYPE)
        self.assertEqual(ref["schema_version"], SCHEMA_VERSION)
        self.assertFalse(ref["claims_iw_acceptance"])
        self.assertEqual(validate_verification_ref_v0(ref), ref)
        resolved = resolve_verification_ref_v0(
            ref, artifact_root=self.artifact_root
        )
        self.assertEqual(
            resolved["verified_artifact"]["extracted"]["verification_result"], "PASS"
        )

    def test_valid_eig_cleanup_result_ref(self) -> None:
        art = _eig_pass_result()
        rel = "results/eig_cleanup_result.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_EIG_CLEANUP_RESULT
        )
        ref = build_verification_ref_v0(
            work_id="work-eig-1",
            verifier="weaver-forge/eig-cleanup-residue-v0",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_EIG_CLEANUP_RESULT,
                "sha256": sha,
                "bytes_length": nbytes,
            },
            verification_type="eig_cleanup_residue_verifier_v0",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            underlying_nonclaims=art["nonclaims"],
        )
        resolved = resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)
        self.assertEqual(resolved["verification_ref"]["verification_result"], "PASS")
        self.assertFalse(resolved["verification_ref"]["claims_iw_acceptance"])

    def test_valid_lifecycle_decision_ref(self) -> None:
        art = _lifecycle_decision(decision="PASS")
        rel = "results/decision.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_LIFECYCLE_DECISION
        )
        ref = build_verification_ref_v0(
            work_id="work-lifecycle-1",
            verifier="weaver-forge/audit_lifecycle",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_LIFECYCLE_DECISION,
                "sha256": sha,
                "bytes_length": nbytes,
            },
            verification_type="audit_lifecycle_decision",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            target_identity="repo:fixture-target",
            target_commit_or_version={
                "binding_kind": "git_commit",
                "value": COMMIT_A,
            },
            underlying_claim_id="P5-PRIMARY",
            underlying_scope={"kind": "claim", "claim_id": "P5-PRIMARY"},
            work_id_adapter_binding={
                "binding_kind": "explicit_adapter",
                "source_identity_field": "claim_id",
                "source_identity_value": "P5-PRIMARY",
                "mapping_note": "deterministic WORLD THIRD work_id adapter binding; underlying artifact unchanged",
            },
        )
        resolved = resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)
        self.assertEqual(
            resolved["verified_artifact"]["extracted"]["verification_result"], "PASS"
        )

    # 2
    def test_wrong_artifact_sha_rejected(self) -> None:
        ref = self._build_from_generic()
        bad = dict(ref)
        aref = dict(bad["verification_artifact_ref"])
        aref["sha256"] = "0" * 64
        bad["verification_artifact_ref"] = aref
        # Self-binding will change — rebuild identity via validate failure on resolve path
        # after fixing sha on a structurally re-built ref:
        art = _generic_verdict(verdict="PASS")
        rel = "results/verdict_sha.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        ref2 = build_verification_ref_v0(
            work_id="work-sha-bad",
            verifier="weaver-forge",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": "0" * 64,
                "bytes_length": nbytes,
            },
            verification_type="weaver_verification_verdict_v0",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            target_identity=art["target_identity"],
            target_commit_or_version=art["target_commit_or_version"],
            underlying_scope=art["scope"],
        )
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "SHA-256"):
            resolve_verification_ref_v0(ref2, artifact_root=self.artifact_root)
        _ = sha  # written artifact sha intentionally unused (mismatch)

    # 3
    def test_wrong_byte_length_rejected(self) -> None:
        art = _generic_verdict(verdict="PASS")
        rel = "results/verdict_len.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        ref = build_verification_ref_v0(
            work_id="work-len-bad",
            verifier="weaver-forge",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": sha,
                "bytes_length": nbytes + 1,
            },
            verification_type="weaver_verification_verdict_v0",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            target_identity=art["target_identity"],
            target_commit_or_version=art["target_commit_or_version"],
            underlying_scope=art["scope"],
        )
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "byte-length"):
            resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)

    # 4
    def test_missing_artifact_rejected(self) -> None:
        art = _generic_verdict(verdict="PASS")
        rel = "results/missing.json"
        # Do not write file; invent length/sha of canonical bytes.
        raw = (
            json.dumps(art, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        sha = hashlib.sha256(raw).hexdigest()
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        ref = build_verification_ref_v0(
            work_id="work-missing",
            verifier="weaver-forge",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": sha,
                "bytes_length": len(raw),
            },
            verification_type="weaver_verification_verdict_v0",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            target_identity=art["target_identity"],
            target_commit_or_version=art["target_commit_or_version"],
            underlying_scope=art["scope"],
        )
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "missing"):
            resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)

    # 5
    def test_malformed_artifact_rejected(self) -> None:
        rel = "results/malformed.json"
        path = self.artifact_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = b"{not-json"
        path.write_bytes(raw)
        sha = hashlib.sha256(raw).hexdigest()
        # Use a placeholder digest — extract will fail after JSON parse.
        fake_digest = "1" * 64
        ref = build_verification_ref_v0(
            work_id="work-malformed",
            verifier="weaver-forge",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": sha,
                "bytes_length": len(raw),
            },
            verification_type="weaver_verification_verdict_v0",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=fake_digest,
        )
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "malformed"):
            resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)

    # 6
    def test_declared_pass_against_non_pass_rejected(self) -> None:
        art = _generic_verdict(verdict="FAIL")
        rel = "results/fail.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        ref = build_verification_ref_v0(
            work_id="work-false-pass",
            verifier="weaver-forge",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": sha,
                "bytes_length": nbytes,
            },
            verification_type="weaver_verification_verdict_v0",
            verification_result="PASS",  # lie
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            target_identity=art["target_identity"],
            target_commit_or_version=art["target_commit_or_version"],
            underlying_scope=art["scope"],
        )
        with self.assertRaisesRegex(
            WorldThirdVerificationRefError, "verification_result does not match"
        ):
            resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)

    # 7
    def test_target_mismatch_rejected(self) -> None:
        ref = self._build_from_generic()
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "target mismatch"):
            resolve_verification_ref_v0(
                ref,
                artifact_root=self.artifact_root,
                expected_target_identity="obj:other-target",
            )

    # 8
    def test_commit_version_mismatch_rejected(self) -> None:
        ref = self._build_from_generic()
        with self.assertRaisesRegex(
            WorldThirdVerificationRefError, "commit/version mismatch"
        ):
            resolve_verification_ref_v0(
                ref,
                artifact_root=self.artifact_root,
                expected_target_commit_or_version={
                    "binding_kind": "git_commit",
                    "value": COMMIT_B,
                },
            )

    # 9
    def test_work_id_required(self) -> None:
        art = _generic_verdict(verdict="PASS")
        rel = "results/need_work.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "work_id"):
            build_verification_ref_v0(
                work_id="",
                verifier="weaver-forge",
                verification_artifact_ref={
                    "artifact_ref": rel,
                    "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                    "sha256": sha,
                    "bytes_length": nbytes,
                },
                verification_type="weaver_verification_verdict_v0",
                verification_result="PASS",
                created_at="2026-09-16T01:00:00Z",
                verification_digest=digest,
            )

    # 10
    def test_rebind_different_work_id_changes_identity(self) -> None:
        ref_a = self._build_from_generic(work_id="work-a", relative="results/a.json")
        ref_b = self._build_from_generic(work_id="work-b", relative="results/b.json")
        self.assertNotEqual(ref_a["verification_ref_id"], ref_b["verification_ref_id"])
        self.assertNotEqual(ref_a["artifact_sha256"], ref_b["artifact_sha256"])
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "work_id rebind"):
            resolve_verification_ref_v0(
                ref_a,
                artifact_root=self.artifact_root,
                expected_work_id="work-b",
            )

    # 11
    def test_claims_iw_acceptance_true_rejected(self) -> None:
        art = _generic_verdict(verdict="PASS")
        rel = "results/iw.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        with self.assertRaisesRegex(
            WorldThirdVerificationRefError, "claims_iw_acceptance=true"
        ):
            build_verification_ref_v0(
                work_id="work-iw",
                verifier="weaver-forge",
                verification_artifact_ref={
                    "artifact_ref": rel,
                    "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                    "sha256": sha,
                    "bytes_length": nbytes,
                },
                verification_type="weaver_verification_verdict_v0",
                verification_result="PASS",
                created_at="2026-09-16T01:00:00Z",
                verification_digest=digest,
                claims_iw_acceptance=True,
            )

    # 12
    def test_normal_weaver_pass_keeps_iw_false(self) -> None:
        ref = self._build_from_generic(verdict="PASS")
        self.assertIs(ref["claims_iw_acceptance"], False)

    # 13
    def test_inconclusive_remains_inconclusive(self) -> None:
        ref = self._build_from_generic(
            verdict="INCONCLUSIVE", relative="results/inconclusive.json"
        )
        self.assertEqual(ref["verification_result"], "INCONCLUSIVE")
        resolved = resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)
        self.assertEqual(
            resolved["verified_artifact"]["extracted"]["verification_result"],
            "INCONCLUSIVE",
        )

    # 14
    def test_partial_remains_partial(self) -> None:
        ref = self._build_from_generic(
            verdict="PARTIAL", relative="results/partial.json"
        )
        self.assertEqual(ref["verification_result"], "PARTIAL")
        resolved = resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)
        self.assertEqual(
            resolved["verified_artifact"]["extracted"]["verification_result"],
            "PARTIAL",
        )

    # 15
    def test_underlying_scope_cannot_be_broadened(self) -> None:
        ref = self._build_from_generic()
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "broaden"):
            resolve_verification_ref_v0(
                ref,
                artifact_root=self.artifact_root,
                expected_scope={
                    "kind": "repository",
                    "covers_entire_repository": True,
                },
            )

    def test_ref_declared_broader_scope_rejected_on_resolve(self) -> None:
        art = _generic_verdict(verdict="PASS")
        rel = "results/scope_broad.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        ref = build_verification_ref_v0(
            work_id="work-scope",
            verifier="weaver-forge",
            verification_artifact_ref={
                "artifact_ref": rel,
                "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                "sha256": sha,
                "bytes_length": nbytes,
            },
            verification_type="weaver_verification_verdict_v0",
            verification_result="PASS",
            created_at="2026-09-16T01:00:00Z",
            verification_digest=digest,
            target_identity=art["target_identity"],
            target_commit_or_version=art["target_commit_or_version"],
            underlying_scope={
                "kind": "repository",
                "covers_entire_repository": True,
            },
        )
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "broaden|scope"):
            resolve_verification_ref_v0(ref, artifact_root=self.artifact_root)

    # 16
    def test_extra_authority_looking_field_rejected(self) -> None:
        art = _generic_verdict(verdict="PASS")
        rel = "results/auth.json"
        sha, nbytes = self._write_artifact(rel, art)
        digest = compute_verification_digest_v0(
            art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
        )
        with self.assertRaisesRegex(
            WorldThirdVerificationRefError, "forbidden authority-looking field|unsupported field"
        ):
            build_verification_ref_v0(
                work_id="work-auth",
                verifier="weaver-forge",
                verification_artifact_ref={
                    "artifact_ref": rel,
                    "artifact_type": ARTIFACT_TYPE_GENERIC_VERDICT,
                    "sha256": sha,
                    "bytes_length": nbytes,
                },
                verification_type="weaver_verification_verdict_v0",
                verification_result="PASS",
                created_at="2026-09-16T01:00:00Z",
                verification_digest=digest,
                human_accepted=True,  # type: ignore[arg-type]
            )

    def test_bytes_matching_is_not_pass_inference(self) -> None:
        """Artifact exists and hashes — still require explicit verdict binding."""
        art = {"note": "bytes only", "claims_iw_acceptance": False}
        rel = "results/bytes_only.json"
        sha, nbytes = self._write_artifact(rel, art)
        with self.assertRaisesRegex(WorldThirdVerificationRefError, "not-bindable"):
            compute_verification_digest_v0(
                art, artifact_type=ARTIFACT_TYPE_GENERIC_VERDICT
            )
        _ = (sha, nbytes)

    # 20-ish noninterference markers for this package
    def test_package_is_additive_namespace(self) -> None:
        self.assertTrue((PACKAGE_ROOT / "verification_ref_v0.py").is_file())
        self.assertTrue(
            (PACKAGE_ROOT / "schemas" / "verification_ref.v0.schema.json").is_file()
        )
        # Must not live under audit_lifecycle / campaign_runner_v0
        self.assertEqual(PACKAGE_ROOT.name, "world_third_v02")


if __name__ == "__main__":
    unittest.main()
