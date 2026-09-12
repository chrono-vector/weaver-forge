# Independence criteria (all mandatory)

1. OPERATOR_INDEPENDENCE
2. ENVIRONMENT_INDEPENDENCE
3. EXECUTION_INDEPENDENCE
4. OBSERVATION_INDEPENDENCE
5. EVIDENCE_GENERATION_INDEPENDENCE
6. RESULT_SUBMISSION_INDEPENDENCE

Designated witness ≠ Independent Witness.
MATCHED ≠ ACCEPTED.
Maintainer dry-run ≠ Independent Witness.
Do not copy operator-derived results as primary proof.

## External submission receipt (required for IW_ACCEPTED)

Receipt fields: SUBMISSION_RECEIPT_ID, SUBMISSION_CHANNEL_CLASS, SUBMISSION_TIMESTAMP,
PACK_DIGEST_RECEIVED, OUTPUT_DIGEST_SUBMITTED, SUBMITTER_ROLE, MAINTAINER_ORIGIN, ACCEPTANCE_ELIGIBLE.

Rules:

- MAINTAINER_ORIGIN must be != YES
- ACCEPTANCE_ELIGIBLE must be YES
- Digests non-empty and matching
- **Self-declared independence alone is insufficient** without a valid external submission receipt
