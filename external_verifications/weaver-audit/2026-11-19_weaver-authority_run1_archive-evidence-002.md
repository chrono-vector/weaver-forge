# Weaver Forge audit authority boundaries — Run #1 evidence record 002

**Date reviewed:** 2026-11-19 JST  
**Verdict:** **WEAVER_AUDIT_UNITTEST_PASS_16 / SELECTED_NONPROMOTION_CONTROLS_PASS / EVIDENCE_ARCHIVE_PASS**. No external or formal IW attestation. No private WORLD THIRD cross-component execution.

## Exact GitHub provenance

- Run: https://github.com/chrono-vector/weaver-forge/actions/runs/44484473264
- Run ID `44484473264`; source commit `b26018efd50fc1883d3e17156dd9c63a78c35132`; development branch `development/independent-verification-v2`.
- Workflow `.github/workflows/weaver-authority-boundaries.yml`.
- Audit job `135424395493`: GitHub `completed/success`.
- Evidence archive job `135424455545`: GitHub `completed/success`.
- GitHub original evidence artifact `weaver-audit-authority-run-evidence`, ID `14509314636`, size `7761` bytes, SHA-256 `af9f45caddca622ffeb01a9cea820724bfdfd824959602822dd7284136588e51`, expires per API `2027-02-17T08:03:55Z`.
- Separate test stdout artifact `weaver-audit-nonpromotion-output`, ID `14509876445`, size `865` bytes, SHA-256 `5dbe5fa772ab86bd1037999c4e5bb3d57eb7c2bb4755f05811cc31bc105e346b`, expires `2026-12-19T08:04:00Z`.
- User-provided uploaded original ZIP `weaver-audit-authority-run-evidence.zip`: size `7761`, SHA-256 `af9f45caddca622ffeb01a9cea820724bfdfd824959602822dd7284136588e51`, matching GitHub artifact digest and size exactly. Outer and nested ZIP CRC checks passed.

## Independently calculated archive hashes

| ZIP entry | Bytes | SHA-256 |
| --- | ---: | --- |
| `RUN_METADATA.txt` | 119 | `4ebce0d1f9da0c9fa80faac10e7a79bceab72ec2004a6c39cfba6343ad770154` |
| `weaver-audit-job.log` | 24243 | `c5b9fc9d16a3082041b30b078010d928bc67a948dcb45335b5af92ed952da35c` |
| `weaver-audit-output.zip` | 865 | `5dbe5fa772ab86bd1037999c4e5bb3d57eb7c2bb4755f05811cc31bc105e346b` |
| `SHA256SUMS.txt` | 260 | `7e8bb1c31c2fd840688602559137cf5d28ee3540032b3d09ea7adbb45e0a56d2` |

All 3 file hashes listed in SHA256SUMS.txt were recomputed from the uploaded ZIP original and matched. The manifest does not list itself.

Inside `weaver-audit-output.zip`: one original `weaver-audit-unittest.txt`, size `2751` bytes, SHA-256 `19135667d5ffeb38b008d6c900f66b4b7225975893a4b3b4800571c35199c0fb`.

## Executed test evidence

Actual archived output states:

```text
Ran 16 tests in 0.153s

OK
```

The real job log contains:

```text
WEAVER_AUDIT_NONPROMOTION=PASS suite=16 boundary_probes=7
```

Individual executed unittest lines report `... ok` for the following seven explicitly targeted tests:

- `test_human_review_blocks_freeze`
- `test_T10_stored_pass_edit_rebound_rejected`
- `test_T11_raw_evidence_semantic_mismatch_rejected`
- `test_T13_FINAL_DECISION_false_promotion_rebound_rejected`
- `test_Pi_B1_freeze_oneshot_survives_deleted_package_dir`
- `test_evidence_tamper_detected`
- `test_boundary_fail_closed`

This is a rerun of Weaver Forge's **existing 16 actual audit lifecycle unit tests** on a synthetic/disposable checkout, not a new test of a real external Work Trace.

## Boundaries and preservation

- The passing tests demonstrate bounded behavior in the reviewed source version for human-review gating, semantic re-verification, evidence-boundary protection, anti-false-promotion and one-shot freeze.
- Not tested: private Job Agent Work Trace signed authority, EIG enforcement, real VECTOR auth, Human/Owner approval, independent Witness qualification, Canonical/Publication authority, or an end-to-end private Integration Harness.
- The binary original ZIP is held as an uploaded file and time-limited GitHub Actions artifact; **this Markdown is only a verification receipt, not permanent binary archival**. Retain a controlled copy and verify SHA-256 when transferred.
- No changes to RC8, main, Ryan's historical material or private repos.
