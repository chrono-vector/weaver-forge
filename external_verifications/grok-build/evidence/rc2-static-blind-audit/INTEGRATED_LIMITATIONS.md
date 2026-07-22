# RC2 static blind audit — integrated limitations

These limitations apply to the RC2 static blind audit as a whole (Batches 1–4 and their integration), independent of the 27 material blockers recorded in `INTEGRATED_BLOCKERS.md`.

| ID | Limitation |
|----|-------------|
| LM-001 | This audit is **static only**. No Docker, Cargo, rustc, rustup, DotSlash, protoc, `ldd`, witness host/container script, or product command was executed at any point. |
| LM-002 | This audit is **not** Independent Witness reproduction. Claim C-014 remains `NOT_STARTED` and is unaffected by this audit's completion. |
| LM-003 | Review was performed against the contents of a single offline transfer bundle (see `TRANSFER_IDENTITY.txt`), not against a live clone of the repository. Findings are scoped to what that bundle contained at the recorded hashes. |
| LM-004 | No independent second reviewer cross-checked these findings; this is a single-pass static review. |
| LM-005 | Runtime, functional, and security properties of the container build, product binary, or validator script are **not** evaluated — only their static text/logic as read. |
| LM-006 | Findings describe defects and gaps as observed in the transferred files; they do not constitute a formal threat model or exhaustive security audit. |
| LM-007 | The 27 blockers in `INTEGRATED_BLOCKERS.md` are believed to be complete for the stated batch themes but are not guaranteed to be an exhaustive enumeration of every possible defect in the reviewed material. |
| LM-008 | This audit does not modify, execute, or remediate any of the reviewed scripts or documents; `INTEGRATED_REMEDIATION_LIST.md` records a remediation **plan** only, not completed remediation. |
| LM-009 | The fixed `rc2` tag and its target commit were treated as immutable inputs; this audit did not move, delete, retag, or otherwise alter them. |
| LM-010 | No commit, push, or tag operation was performed as part of producing this preservation record. |

## What this audit does not establish

- Package readiness `PASS`
- Independent Witness reproduction or C-014 progress of any kind
- That the reviewed scripts would succeed, fail, or behave as described if actually executed
- Completion of remediation for any of the 27 recorded blockers
