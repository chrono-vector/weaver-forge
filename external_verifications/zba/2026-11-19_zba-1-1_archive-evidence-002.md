# ZBA 1.1 — Run #1 archived evidence verification 002

**Reviewed:** 2026-11-19 JST  
**Verdict:** **PINNED_REFERENCE_REPLAY_PASS / ADDED_NEGATIVE_CONTROL_PASS / ARCHIVE_MANIFEST_PASS**, limited to the specified tests. **Not independent formal scientific or security certification.**

## Verifiable provenance
- External source: `ResearchForumOnline/research@c13c6ffe58850216124f9b58fa8185c5c03d7a5d` (tag `zba-v1.1.0`).
- Weaver Forge workflow commit: `96dc639b7e102095ee9fa7bc536b457190c1f78c`.
- GitHub Actions: https://github.com/chrono-vector/weaver-forge/actions/runs/44480524971; run ID **44480524971**.
- Replay job **135411356722**: `completed/success`.
- Archive job **135411422952**: `completed/success`.
- Archive artifact `zba-1-1-run-evidence`, ID **14508386604**, GitHub digest `sha256:26c5d6f7a77ade4e462597634015c8d0bd2b13e5f26a08523efaca9c26fdf1f0`, byte size **7959**, advertised expiry **2027-02-17 07:33:25 UTC**.
- Inner result artifact `zba-1-1-reference-output`, ID **14508696864**, digest `sha256:55e69b2fc924093fbc932d9a9429dc9dd525e07d76c68920cddb2eca190da86a`, expiry **2026-12-19 07:33:31 UTC**.
- Supplied original ZIP `zba-1-1-run-evidence.zip`: **7959 bytes** and SHA-256 **26c5d6f7a77ade4e462597634015c8d0bd2b13e5f26a08523efaca9c26fdf1f0**, exactly matching GitHub artifact metadata. ZIP CRC integrity passed.

## Original archive SHA-256 inventory
| ZIP entry | Bytes | SHA-256 |
| --- | ---: | --- |
| `RUN_METADATA.txt` | 184 | `32746be46e2934605f7662e46e6a81cba1c35263b4f1add91d33c10a9be0a54d` |
| `zba-replay-job.log` | 21019 | `00f1f061d04c88e729f06ac3ccae90cb6de9d25af868917b13bf96b2ef770d75` |
| `zba-1-1-reference-output.zip` | 1939 | `55e69b2fc924093fbc932d9a9429dc9dd525e07d76c68920cddb2eca190da86a` |
| `SHA256SUMS.txt` | 263 | `349773b6d1bfb6a845ed290db5e90ebd9f1b610e05d79e75325b990cc0a3ef68` |

All 3 SHA256SUMS.txt listed source files matched independently. The manifest itself is not listed in the manifest. Inner ZIP CRC passed and contained:

| Inner entry | Bytes | SHA-256 |
| --- | ---: | --- |
| `zba-reference-stdout.json` | 2865 | `7966f7ec559c270b8973bfcf910e81fc4c62287786fb948730da9628f124e1da` |
| `property-check-results.json` | 2865 | `7966f7ec559c270b8973bfcf910e81fc4c62287786fb948730da9628f124e1da` |
| `test-vectors.json` | 3906 | `630f451533699adc55b3adf5b508e87f1ee4d4e1a673541a4ae81456befda952` |

## Results from actual archived stdout and result JSON
- `spec=zba-evidence/1.1`; `state_count=144`.
- `mirror_involution_pass=144`, `reset_idempotence_pass=144`, `mirror_reset_commutation_pass=144`.
- One six-record reference chain accepted, `valid=true`, `records_checked=6`.
- `mutation_count=14`, `mutations_detected=14`; all published negative cases rejected.
- The real archived job log contains `ZBA_REPLAY=PASS states=144 mirror=144 reset=144 commute=144 valid_chain=6 mutations=14/14`.
- The real archived job log contains `ZBA_EXTRA_NEGATIVE_CONTROL=PASS last-record operation tampering detected`, testing a deep-copy last-record operation mutation using the **same reference verifier**.

## Limits and preservation
This establishes exact-input reproducibility and a bounded extra tamper probe, not independent implementation of the verifier, peer review, signature or AEAD security, legal provenance, authenticated real-world record origins, or a formal witness pass. Source is publicly authored by the original researcher and the extra test invokes that reference verifier.

This Markdown receipt stores SHA-256/provenance **but not the original binary ZIP**. Retain original archive elsewhere before Actions expiry and verify its digest after transfer. Historical RC8, main, other receipts, Ryan material, and ASIN-HHC records remain unchanged.

**Status of record 001:** the execution gap is closed for the specific GitHub run #1; broader ZBA qualification remains open.
