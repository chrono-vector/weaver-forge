# WITNESS_STATEMENT.md — required fields (evidence_schema_version=1, RC6-R6 / rc6.5)

This file is authored by the independent Witness. The `key=value` lines below
are structurally validated; surrounding prose is for human review.

RC6-R6 (R6-M2): central refs to package identity and final binding, plus direct
critical equality bindings to the authoritative R3–R5 tuple. Values are copied
from authoritative package records only — never generated, repaired, inferred,
substituted, or overridden here.

Timing (RC4B-033/034): execution_* fields copy BUILD_TIMING.txt
`docker_started_utc` / `docker_finished_utc` exactly (UTC `Z` grammar).

Independence attestations must all be `yes`. product_executed and ldd_used
must be exactly `NO`, and upstream_product_commands_not_run must be `yes`.
If ai_assistance_used=yes, a non-empty ai_assistance_detail is required.
human_review_completed must be `yes`.

```
evidence_schema_version=1
run_id=<run-id-token>
package_identity_ref=WEAVER_FORGE_PACKAGE_IDENTITY.txt
final_binding_ref=WEAVER_FORGE_FINAL_BINDING.txt
authoritative_outcome=<from WEAVER_FORGE_FINAL_BINDING.txt>
artifact_sha256=<from ARTIFACT_IDENTITY / final binding>
evidence_manifest_ref=EVIDENCE_MANIFEST.sha256
statement_identity_sha256=<sha256 of fixed critical binding payload>
deviations_sha256=<sha256 of DEVIATIONS.txt>
deviation_state=NONE
redactions_index_sha256=<sha256 of REDACTIONS_INDEX.txt>
redaction_state=NONE
final_machine_ceiling=<validator-authoritative ceiling>
execution_date_utc=<YYYY-MM-DD from docker_started_utc>
execution_started_utc=<from BUILD_TIMING.txt docker_started_utc>
execution_finished_utc=<from BUILD_TIMING.txt docker_finished_utc>
execution_timing_source_file=BUILD_TIMING.txt
execution_timing_source_start_field=docker_started_utc
execution_timing_source_end_field=docker_finished_utc
witness_identity_or_handle=<name or public handle>
not_package_owner=yes
not_owner_side_reproducer=yes
witness_controlled_host=yes
ai_assistance_used=no
ai_assistance_detail=
human_review_completed=yes
product_executed=NO
ldd_used=NO
upstream_product_commands_not_run=yes
```
