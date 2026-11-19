# Weaver audit / WORLD THIRD authority boundary — source scope 001

**Date:** 2026-11-19 JST
**Status:** **NOT VERIFIED (new CI execution and log evidence outstanding)**.

## Reviewed real implementation

- Weaver public `audit_lifecycle/orchestrator.py` implements request, boundary, baseline, pin, execution, raw evidence, control vectors, decision, human review, freeze, semantic re-verification and digest binding.
- Weaver `audit_lifecycle/tests/test_lifecycle.py` has 16 actual unittest methods. In particular, reviewed names cover `test_human_review_blocks_freeze`, `test_T10_stored_pass_edit_rebound_rejected`, `test_T11_raw_evidence_semantic_mismatch_rejected`, `test_T13_FINAL_DECISION_false_promotion_rebound_rejected`, `test_Pi_B1_freeze_oneshot_survives_deleted_package_dir`, `test_evidence_tamper_detected`, and `test_boundary_fail_closed`.
- The `audit_lifecycle` tests use temporary synthetic input and probe the **existing code**, not a new surrogate verifier.
- Existing `.github/workflows/independent-verification-v2.yml` already runs the baseline suite on Ubuntu and Windows. The new workflow is an **evidence-focused repeat** with a separate bounded archive, not a new integration implementation.

## New workflow

`.github/workflows/weaver-authority-boundaries.yml`:
- On development branch push for this workflow only, or manual dispatch.
- Executes the existing complete lifecycle unittest suite, demands 16 tests and the named seven important tests, and retains real stdout.
- Archives the completed original job log, output artifact ZIP, run source metadata and SHA-256 checksum manifest in a 90-day Actions artifact.
- No freeze or Human acceptance action is carried out on real operational evidence. Test fixture approval steps only occur in temporary disposable directories under the unit tests.

## Reviewed authority boundary

- Private Job Agent `world-third-private-job-agent` README describes FIND/INTAKE and Work Trace roles and explicit separation of authorization, enforcement, execution, Weaver verification, Human, Independent Witness, Canonical and Publication.
- Private Integration Harness `world-third-private-integration-harness` README describes a continuous synthetic work_id chain requiring sibling private checkouts, EIG, and local-only ignored runtime evidence; it **must not be published in public Weaver artifacts**.
- Existing private v0.4 completion record claims historical owner acceptance, separate from this audit.
- We have NOT run real end-to-end Job Agent → EIG → VECTOR → Weaver integration; **INCOMPLETE**, not PASS.
- The public workflow does not access private Job Agent code, real Work Trace, private keys, Owner records, or private harness artifacts.

## Next gate

Retrieve exact GitHub Actions run ID and successful per-step evidence, original job log and ZIP manifest SHA-256. Confirm `Ran 16 tests` and `WEAVER_AUDIT_NONPROMOTION=PASS` in actual logs before reporting bounded PASS. If run fails, investigate and preserve failure as evidence; never silently replace prior records.

No changes to RC8, main, Ryan's historic files, original receipts, or private repositories.
