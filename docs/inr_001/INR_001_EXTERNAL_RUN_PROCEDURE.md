# INR-001 External Run Procedure v0

Status: PROCEDURE_ONLY_NOT_EXECUTED

This procedure is for a future materially non-origin run. Local tests of INR tooling do not close the non-origin reconstruction event.

1. Use only the trusted INR configuration for target/profile/origin bindings.
2. Create a unique INR event ID and single-use run challenge before target execution.
3. Acquire the frozen PSM-001 target independently from the frozen source.
4. Verify source/archive and distribution byte digests.
5. Establish a qualifying v0 environment: separate physical machine or fresh hosted runner outside the origin runner boundary.
6. Ensure no shared mutable origin workspace, cache, volume, filesystem, package/build cache, snapshot, or Git object store is used.
7. Create a fresh staging directory, build the protected execution tree, measure it, make it read-only/effectively immutable, and check aliases/symlinks/parents/mounts.
8. Record Python, import, Git, protected-set, and non-origin evidence.
9. Start trusted capture. Capture must itself launch each target process and directly capture stdout/stderr/exit status.
10. Execute every required profile case in frozen order.
11. Preserve every command result with event ID, challenge, sequence, command ID, stdout/stderr hashes, return code, and process provenance.
12. Complete post-execution measurement and CAPTURE_COMPLETE.
13. Steps 2-12 are performed only by the trusted supervisor process (r3):
    `python -m docs.inr_001.capture_inr_v0 --event-id ID --repository REPO --out EXPORT.json [--ledger PATH] [--work-dir DIR]`
    launches `python -I -S -B <worktree>/docs/inr_001/supervisor_inr_v0.py` with these non-trust parameters
    only and relays its report after checking that the report is bound to the launched process (pid, event ID,
    exit status). The operator may also start the supervisor directly with the same interpreter flags and
    arguments. The supervisor reserves the event/challenge in the persistent ledger, launches every child
    itself, derives the result in the same execution and writes the export. It accepts no evidence, snapshot,
    capture record or report from argv, stdin, environment or files.
    `python -m docs.inr_001.validate_inr_v0 EXPORT.json [--ledger PATH]` only re-checks a disk export
    (INFORMATIONAL_RECHECK: schema, ledger, stream digests) and can never yield PASS.
    The ledger must live in an independently protected location. Its head record catches truncation of the
    ledger alone, but deleting the ledger and its head together cannot be detected locally (not tamper evidence).
14. Classify according to the supervisor report only. In v0, non-origin, shared-state absence and all-writer
    isolation are always UNCONFIRMED, so the overall result cannot be PASS. Do not claim IW acceptance,
    Human Final, or production permission. The profile does not claim that PSM rejects a positive
    production-permission assertion.

Nonclaims: this procedure is not an implementation proof, not an INR PASS, not IW admission, and not production authorization.
