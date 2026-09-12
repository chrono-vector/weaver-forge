# Failure handling

Categories: REPRODUCTION_PASS, REPRODUCTION_MISMATCH, ENVIRONMENT_BLOCKED, DEPENDENCY_BLOCKED, RPC_BLOCKED, SOURCE_MISMATCH, RUNTIME_MISMATCH, UNEXPECTED_RESULT, WITNESS_ABORTED.

Rules:
- Failed attempts must not be deleted or silently overwritten
- Retries append to retry-log with prior_failure_id
- Later PASS does not erase earlier failure
