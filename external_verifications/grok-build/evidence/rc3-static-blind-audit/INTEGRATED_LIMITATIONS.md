# RC3 static blind audit — integrated limitations

These limitations apply to the RC3 static blind audit as a whole (Batches 1–4 and their integration), independent of the 28 material blockers recorded in `INTEGRATED_BLOCKERS.md`.

| ID | Limitation |
|----|-------------|
| LM-001 | This audit is **static only**. No Docker, Cargo, rustc, rustup, DotSlash, protoc, `ldd`, witness host/container script, or either Witness script referenced by the runbook, or product command was executed at any point. |
| LM-002 | This audit is **not** Independent Witness reproduction. Claim C-014 remains `NOT_STARTED` and is unaffected by this audit's completion. |
| LM-003 | Review was performed against the contents of a single offline transfer bundle (see `TRANSFER_IDENTITY.txt`), not against a live clone of the repository. Findings are scoped to what that bundle contained at the recorded hashes. |
| LM-004 | No independent second reviewer cross-checked these findings; this is a single-pass static review. |
| LM-005 | Runtime, functional, and security properties of the container build, product binary, or validator script are **not** evaluated — only their static text/logic as read. |
| LM-006 | Findings describe defects and gaps as observed in the transferred files; they do not constitute a formal threat model or exhaustive security audit. |
| LM-007 | The 28 blockers in `INTEGRATED_BLOCKERS.md` are believed to be complete for the stated batch themes but are not guaranteed to be an exhaustive enumeration of every possible defect in the reviewed material. |
| LM-008 | This audit does not modify, execute, or remediate any of the reviewed scripts or documents; `INTEGRATED_REMEDIATION_LIST.md` records a remediation **plan** only, not completed remediation, for the 28 blockers themselves. |
| LM-009 | The fixed `rc3` tag and its target commit, and the prior immutable `rc1`/`rc2` tags, were treated as immutable inputs; this audit did not move, delete, retag, or otherwise alter any of them. |
| LM-010 | No commit, push, or tag operation was performed as part of producing this preservation record. |
| LM-011 | This audit does not reopen, revise, or supersede the rc1 or rc2 audit verdicts (both `NOT READY`); it is a new, independent static review of the distinct rc3 identity. |
| LM-012 | This audit does not prepare, draft, or cut a `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4` successor tag; successor identity preparation is recorded only as required future work. |

## What this audit does not establish

- Package readiness `PASS`
- Independent Witness reproduction or C-014 progress of any kind
- That the reviewed scripts would succeed, fail, or behave as described if actually executed
- Completion of remediation for any of the 28 recorded blockers
- Creation, preparation, or readiness of a `1.0.0-rc4` successor package or tag
