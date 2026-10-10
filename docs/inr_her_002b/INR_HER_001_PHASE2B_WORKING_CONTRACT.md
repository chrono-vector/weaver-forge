# INR-HER-001 Phase 2B Working Contract

Status: PHASE2B_WORKING_CONTRACT

This document is the working contract for one additive gate. It is not a Human Final, not production authority, and not an external-run admission.

FULL_INR_READY: NO

Accepted Phase 2A Human Final: `95ec95fd2273c303123ed5a42ba98a786ae0a679`

Phase 2A implementation: `ef29776326a4f9d3cfcb6847515cd160cd5ef519`

Accepted Phase 1 Human Final: `fccd128ec37a8cfb940c572a1bf566449abddb25`

Accepted Phase 1, Phase 2A, r3, and AWI files stay byte-for-byte with that Human Final. N1 and N2 stay unresolved.

## Five separate layers

Structured BLOCKED outcomes are objects returned by `evaluate_phase2b`. `overall_status` is FAIL, BLOCKED, or UNCONFIRMED. The function does not raise for invalid privileges, invalid claimed_status, a non-dict observation, a hostile observation key, or a malformed Phase 2A result. It does not emit PASS.

Schema-level validation is `schema_check` over the closed vocabulary in `docs/inr_001/schema_check.py`: type, const, enum, properties, required, additionalProperties, items, minItems, minLength, and pattern. That vocabulary has no `uniqueItems` and no `maxItems`. `assert_schema_contract` rejects those keywords. A Phase 2A or Phase 2B checks array can repeat a legal entry and still pass schema validation.

Runtime check-inventory enforcement is authoritative. The Phase 2A inventory is the ordered list `schema_version`, `platform`, `cpython_identity`, `cpython_pin`, `mingit_identity`, `mingit_pin`, `privileges`, `git_execution_path`, `git_config`, `event_freshness`, `claim_boundary`. The Phase 2B inventory is the ordered list `n3_privileges`, `n3_claimed_status`, `n4_check_inventory`, `phase2a_delegation`, `isolation_boundary`. Each entry is an object with exactly `check_id`, `status`, and `reason`. `status` is FAIL, BLOCKED, or UNCONFIRMED. `reason` is a non-empty string. Missing, repeated, unexpected, reordered, and malformed entries are rejected. `inventory_authority` is `RUNTIME`. `schema_uniqueness` is `NOT_ESTABLISHED`.

Actual isolation evidence is not produced. `isolation_evidence` is `NOT_ESTABLISHED`. No returned check uses PASS. `HASH_AGREEMENT_ONLY` is not freshness and not isolation. This phase does not create a token, Job, ACL, or Git-ownership proof.

Nonclaims inherited from Phase 2A remain in force, together with the Phase 2B additions below. Accepting this gate does not reopen those verdicts.

## N3 input gate

`privileges` and `claimed_status` are classified before `evaluate_phase2a` is called.

Supported privileges are the exact strings `ABSENT`, `UNOBSERVED`, `PRESENT_UNEXERCISED`, and `ENABLED`. A missing `privileges` key is supported. Every other present value is rejected, including lists, dicts, sets, tuples, bytes, numbers, booleans, `None`, string subclasses, and strings outside those four.

Supported `claimed_status` is an exact `str`, including the Phase 2A pass-claim strings. A missing key is supported. Lists, dicts, sets, tuples, bytes, numbers, booleans, `None`, and string subclasses are rejected. A rejected claim is not recorded as `HER_NO_PASS_CLAIM`.

`observation is None` is the supported omitted observation. Any other non-dict is rejected and is not replaced with `{}`.

An exact dict is supported only when every key is an exact `str`. Phase 2B copies that mapping once, by `items()`, into a new dict before it reads `privileges` or `claimed_status` and before it calls `evaluate_phase2a`. A non-string key is rejected by `type` during that copy. Its `__eq__` and `__hash__` are not called. The copy is the mapping Phase 2A receives, so a later write to the caller's dict is not visible to Phase 2A. Value objects are not deep-copied: accepted Phase 2A still compares those same objects, and a value can still change its own state. A deep conversion would change that accepted behavior, so it is not done. If building or classifying the copy raises `Exception`, including `TypeError`, `ValueError`, or `RecursionError`, the rejection is `HER_OBSERVATION_INPUT_REJECTED`. `BaseException`, including `KeyboardInterrupt` and `SystemExit`, is not caught.

Rejection reasons, in priority order, are `HER_OBSERVATION_INPUT_REJECTED`, `HER_PRIVILEGE_INPUT_REJECTED`, and `HER_CLAIMED_STATUS_INPUT_REJECTED`. The result does not echo the rejected value. `phase2a_delegated` is false.

Supported inputs are delegated through that owned mapping. Their overall status and reason remain the Phase 2A result. That preservation is not an isolation PASS.

## N4 inventory gate

After a supported call returns, Phase 2B reads that object once and builds an owned plain snapshot. The snapshot accepts only exact `dict`, `list`, `str`, `bool`, and `None` values. It does not use `deepcopy`. It does not call a caller-defined `__eq__` or `__hash__`. Nested `checks` and `pins` are copied in that same walk. A nested value whose type is not the schema leaf is not followed, so a cycle ends as a malformed or rejected snapshot instead of a recursive walk. Strings, booleans, and `None` may be reused because they are immutable. Dicts and lists in the snapshot are new objects. After the snapshot function returns, inventory validation, schema validation, status and reason checks, and the Phase 2B output use only the snapshot. There is no later read of the original Phase 2A result. This does not bound CPU or memory use. Schema success is not consulted as a uniqueness proof. These results are distinct:

- `HER_CHECK_INVENTORY_REJECTED`: the check list is missing, repeated, unexpected, reordered, or malformed. `n4_inventory` is `REJECTED`. The list is not copied. `phase2a_overall_status` is `BLOCKED` and `phase2a_overall_reason` is `HER_CHECK_INVENTORY_REJECTED`. The untrusted `overall_status` and `overall_reason` are not copied.
- `HER_PHASE2A_PASS_FORBIDDEN`: the check list matches the runtime inventory and `overall_status` is outside FAIL, BLOCKED, and UNCONFIRMED. `n4_inventory` stays `ACCEPTED`. The result is still BLOCKED, and no PASS status is stored.
- `HER_PHASE2A_RESULT_REJECTED`: the returned object is not a usable Phase 2A result. A non-string key at the top level or under `pins`, a pins or nonclaims value that is not an exact schema leaf, or any other unsupported structure is this reason. When the check list was not confirmed, including a non-dict result or an `Exception` raised while building the snapshot, `n4_inventory` is `REJECTED`. When the snapshotted check list already matched and a later field is unsupported or fails `schema_check`, `n4_inventory` is `ACCEPTED`. A non-string key inside a check is malformed inventory, not this reason: its type is visible without calling the key, so the check list is classified as `HER_CHECK_INVENTORY_REJECTED`. These catches are not a blanket around Phase 2B. `BaseException`, including `KeyboardInterrupt` and `SystemExit`, is not caught. `phase2a_overall_status` is `BLOCKED` and `phase2a_overall_reason` is `HER_PHASE2A_RESULT_REJECTED`. The untrusted `overall_status` and `overall_reason` are not copied.
- `HER_PHASE2A_RESULT_CONTRADICTION`: the result is schema-valid and its check list matches the runtime inventory, but it cannot be an accepted Phase 2A ranking. Each check status and reason must be a pair emitted by that check in `preflight_her_v1.py`. `phase1_overall_status` `NOT_DELEGATED` requires reason `NOT_DELEGATED` and adds no ranking contribution. Any other Phase 1 status contributes its reason. Overall status and reason must then equal the accepted Phase 2A priority rule, including an unknown reason sorting ahead of known reasons inside one status. `PASS`, `HASH_AGREEMENT_ONLY`, `FRESH`, `ISOLATION_PASS`, and `FULL_INR_PASS` are not result reasons. `n4_inventory` stays `ACCEPTED`. The forged reason is not copied.
- `HER_PHASE2A_UNSTRUCTURED_ERROR`: Phase 2A raised. The exception text is not copied. `n4_inventory` is `NOT_RUN`.

`ACCEPTED` on `n4_inventory` means only that the check list matched the runtime inventory. It does not mean the schema guarantees uniqueness, and it does not mean isolation.

For `HER_CHECK_INVENTORY_REJECTED` and `HER_PHASE2A_RESULT_REJECTED`, the Phase 2B `overall_status` stays `BLOCKED` and the Phase 2B `overall_reason` stays that rejection. The stored Phase 2A verdict uses the same fixed pair already used when those fields are not usable: `phase2a_overall_status` `BLOCKED` and `phase2a_overall_reason` equal to the Phase 2B rejection. No untrusted status or reason is stored, including `PASS`, `HASH_AGREEMENT_ONLY`, `ISOLATION_PASS`, `FULL_INR_PASS`, and any other caller string. `phase2a_checks` is empty. `NOT_DELEGATED` remains the sentinel only when `phase2a_delegated` is false. An accepted Phase 2A result still copies its overall status, reason, and checks from the snapshot. Those copied checks are new dicts in a new list. Mutating the caller's result after the snapshot does not change them, and mutating the returned checks does not change the caller's result.

`n4_inventory` `ACCEPTED` describes the snapshotted check list only. A check list that is repeated, reordered, or extended after that copy is not given `ACCEPTED`, and it is not published. No rejection echoes an untrusted value. No returned status is `PASS`.

## Exception boundary

`evaluate_phase2b` catches `Exception` in these places, and nowhere else:

- Building and classifying the observation snapshot, after the `None` and non-dict checks.
- Building the Phase 2A snapshot. An `Exception` there means the check list was not confirmed, so `n4_inventory` is `REJECTED`.
- `schema_check` of that snapshot, only after the snapshotted inventory matched. An `Exception` there keeps `n4_inventory` `ACCEPTED`.

The rank and contradiction rules then run on the snapshot. Those rules are outside the catch. `_seal` is outside the catch: an internally invalid Phase 2B result still raises `RuntimeError`. The existing `Exception` boundary around `evaluate_phase2a` is unchanged and still returns `HER_PHASE2A_UNSTRUCTURED_ERROR`. `SystemExit` and `KeyboardInterrupt` raised by `evaluate_phase2a` still propagate. Accepted `schema_check` is not edited.

Caller-defined key methods are not used to read the Phase 2A result or the observation mapping. A `SystemExit` stored on such a key therefore does not run. `MemoryError` and other ordinary `Exception` values raised while building a snapshot or while checking the snapshot's schema become the structured BLOCKED result for that step. `KeyboardInterrupt`, `SystemExit`, and any other `BaseException` that actually leaves called code still propagate. This boundary does not limit CPU or memory use, and it does not change the accepted Phase 1 direct-entry `TypeError`. `phase2a_inventory_errors`, called directly rather than through `evaluate_phase2b`, is outside this snapshot and can still raise.

## Inherited limits

N1 remains the accepted Phase 2A behavior. An unhashable `schema_version` is delegated to Phase 2A, which returns BLOCKED `HER_SCHEMA_VERSION` and does not call Phase 1. The Phase 1 edit remains `STOPPED`.

N2 remains `UNEXECUTED`. Hash agreement, uniform relabeling, replay resistance, and authenticated head binding are not established.

Python 3.11.9 SHA-256 remains `PIN_PENDING`. The MinGit digest remains `UNRATIFIED`. Privileged Windows token, Job, ACL, and Git-ownership isolation remains unverified. Git runtime and config closure remain unproven. Writers outside trust base T remain unconfirmed. Independent Witness remains unclaimed. No external reconstruction run is performed. No FULL INR PASS is claimed. No production authority is claimed.

## Nonclaims recorded on every result

- `phase1_source_edited`
- `restricted_token_isolation`
- `job_containment`
- `event_freshness`
- `independent_external_witness`
- `full_inr_pass`
- `human_final`
- `production_authority`
- `external_run`
- `python_3_11_9_sha256_ratified`
- `mingit_digest_ratified`
- `privileged_windows_tests_executed`
- `n1_phase1_typeerror_fixed`
- `n2_freshness_binding`
- `schema_only_check_uniqueness`
- `isolation_evidence`
- `accepted_history_reopened`
