# INR-001 Final Closure Addendum

Status: FINAL_DESIGN_FREEZE_FROZEN

Mode: Documentation persistence only.

This document preserves the final INR-001 design closure addendum. It does not implement INR-001, does not execute a non-origin reconstruction event, does not create Independent Witness admission, does not create Human Final, and does not grant production permission.

## Trusted origin reference binding

Frozen invariant:

```text
TARGET_SHA
→ ACCEPTED_ORIGIN_REFERENCE_SET_ID
→ ACCEPTED_ORIGIN_REFERENCE_SET_DIGEST
```

For INR v0, this mapping must live in trusted INR verifier/configuration, not in the executor-controlled event.

The executor may only reference the accepted origin set.

The verifier must reject PASS if:

- origin set ID is unknown
- origin set digest mismatches
- executor supplies an alternate origin set
- required origin entry is missing
- target SHA maps to more than one active accepted origin set
- accepted origin mapping was changed after EVENT_START
- origin coverage cannot be established

If the correct origin set cannot be established: `UNCONFIRMED`.

Event data must not create, select, weaken, or redefine origin truth.

Closure status: `CLOSED`.

## Trusted capture / target-process binding

Frozen invariant:

```text
CURRENT EVENT
→ CURRENT RUN CHALLENGE
→ CAPTURE PROCESS
→ TARGET PROCESS START
→ TARGET PROCESS EXECUTION
→ DIRECT STDOUT/STDERR CAPTURE
→ EXIT STATUS
→ EVENT COMPLETE
```

Trusted capture must itself launch and observe the target execution for the current INR event.

PASS requires direct binding across the full chain above. The capture mechanism must not merely read historical output files.

Required:

- target process launched after EVENT_START
- target process launched after current challenge binding
- execution occurs within FREEZE_START → CAPTURE_COMPLETE
- stdout/stderr captured directly from that execution
- exit status obtained from that execution
- process execution provenance bound to current event
- EVENT_COMPLETE occurs only after target process completion

If target-process execution provenance is absent: `UNCONFIRMED`.

Closure status: `CLOSED`.

## Run challenge single-use rule

`RUN_CHALLENGE_VALUE` must be:

- generated before target execution
- unique for the event
- single-use
- bound to exactly one `INR_EVENT_ID`
- rejected if already used by another completed/in-progress event

Challenge reuse: PASS forbidden.

Changing `event_id` while reusing challenge: PASS forbidden.

Closure status: `CLOSED`.

## Old-evidence replay rejection rule

Reject PASS if:

- target process was not launched in current event
- stdout/stderr came only from historical files
- process result predates EVENT_START
- evidence was copied from a prior event
- wrapper metadata is fresh but child execution provenance is absent
- challenge was injected after execution
- challenge/event binding is replayed

Same stdout bytes may legitimately recur, but execution provenance must be current-event provenance.

Closure status: `CLOSED`.

## Cumulative material finding state

The cumulative material finding ledger is preserved in:

`docs/inr_001/INR_001_CLOSURE_MATRIX.md`

Summary:

- `CUMULATIVE_MATERIAL_FINDINGS_TOTAL: 18`
- `CUMULATIVE_MATERIAL_FINDINGS_CLOSED: 18`
- `CUMULATIVE_MATERIAL_FINDINGS_OPEN: 0`
- `REMAINING_MATERIAL_DESIGN_GAPS: NONE`
- `FINAL_DESIGN_FREEZE: FROZEN`
- `READY_FOR_IMPLEMENTATION: NO`

## Boundary / nonclaims

This documentation persistence commit does not mean:

- INR implementation exists
- INR non-origin reconstruction has run
- local INR tooling has passed
- independent reconstruction has passed
- Independent Witness admission exists
- Human Final exists
- production readiness exists
- production permission exists
- PSM-001 or any CLOSED scope was modified

STOP.
