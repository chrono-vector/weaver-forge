# WITNESS_STATEMENT.md — required fields (evidence_schema_version=1, 1.0.0-rc4)

This file is authored by the independent Witness. The `key=value` lines below
are structurally validated; surrounding prose is for human review.

Independence attestations must all be `yes`. product_executed and ldd_used
must be exactly `NO`, and upstream_product_commands_not_run must be `yes`
(the Witness never ran the product binary or any upstream product command,
and never invoked `ldd` on the artifact). If ai_assistance_used=yes, a
non-empty ai_assistance_detail is required. human_review_completed must be
`yes`.

```
evidence_schema_version=1
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
