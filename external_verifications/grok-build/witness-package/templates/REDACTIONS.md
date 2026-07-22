# REDACTIONS.md — required fields (evidence_schema_version=1)

Fields below are parsed as `key=value` lines by the validator regardless of
surrounding markdown headings. Keep the exact field names.

evidence_schema_version=1

# redaction_state must be exactly NONE or PRESENT.
redaction_state=NONE

semantic_integrity_declaration=yes

# If redaction_state=PRESENT, enumerate each redaction with a unique index
# <n> and provide all four fields below for every index:
#
#   redaction_<n>_file=<evidence filename containing the redaction>
#   redaction_<n>_field=<field or line redacted>
#   redaction_<n>_reason=<why this needed redaction>
#   redaction_<n>_replacement_marker=[REDACTED: reason]
#
# The replacement marker must be a visible `[REDACTED: ...]` string left in
# place of the removed value (never silently delete a field).
#
# Never redact: commits, digests, exact commands, exit codes, artifact
# SHA-256/size, or independence statements. The validator rejects any
# redaction whose file/field/reason text references these prohibited
# categories.
#
# Example (delete if redaction_state=NONE):
# redaction_1_file=ENVIRONMENT.txt
# redaction_1_field=host_docker_client_version
# redaction_1_reason=Contains internal build number unrelated to the pin
# redaction_1_replacement_marker=[REDACTED: internal build number]
