# Failure handling

Categories: REPRODUCTION_PASS, REPRODUCTION_MISMATCH, ENVIRONMENT_BLOCKED, DEPENDENCY_BLOCKED, RPC_BLOCKED, SOURCE_MISMATCH, RUNTIME_MISMATCH, UNEXPECTED_RESULT, WITNESS_ABORTED.

Rules:

- Failed attempts must not be deleted or silently overwritten
- Retries append to retry-log with prior_failure_id / PRIOR_ATTEMPT_ID
- Later PASS does not erase earlier failure
- ATTEMPT_ID policy: retain identifiers across attempts

## Assurance

- `FAILURE_HISTORY_ASSURANCE` = `SUBMITTED_HISTORY_PRESERVED`
- Never claim `COMPLETE_HISTORY_CRYPTOGRAPHICALLY_PROVEN`
