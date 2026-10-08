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
12. Complete post-execution measurement and EVENT_COMPLETE.
13. Steps 2-12 are performed by the fused local entry point only:
    `python -m docs.inr_001.capture_inr_v0 --event-id ID --repository REPO --out EXPORT.json [--ledger PATH]`.
    It reserves the event/challenge in the persistent ledger, launches every child itself and verifies the
    live evidence in the same process. `python -m docs.inr_001.validate_inr_v0 EXPORT.json [--ledger PATH]`
    only re-checks an export (schema + ledger) and can never yield PASS.
14. Classify according to the live verifier result. In v0, non-origin, shared-state absence and all-writer
    isolation are always UNCONFIRMED, so the overall result cannot be PASS. Do not claim IW acceptance,
    Human Final, or production permission.

Nonclaims: this procedure is not an implementation proof, not an INR PASS, not IW admission, and not production authorization.
