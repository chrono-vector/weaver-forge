# INR-HER N2 Design Freeze v0

VERDICT:
HUMAN_DESIGN_FREEZE_ACCEPTED

HUMAN_APPROVAL:
GRANTED

SCOPE:
Responsibility separation and trust-boundary principles only.

ACCEPTED_BASELINE:
468f0bfecca2f3f157928801caa64680e766692d

## Four responsibilities

ISSUER:
An external authority responsible for authenticating event_id, a fresh nonce, issue time, source head and each surface freeze hash.

VERIFIER:
An independently established verification authority using a trusted verification key not controlled by the HER supervisor.

NONCE HOLDER:
An external holder responsible for checking whether a nonce has already been used and recording accepted nonce consumption.

CLOCK AUTHORITY:
An independently defined trusted time source for issue-time and expiry checks.

## Trust boundaries

- The HER supervisor must not self-issue its own freshness evidence.
- The verification trust anchor must not be derived solely from event bytes or supervisor-local state.
- Nonce replay protection requires independently controlled persistent state.
- Local timestamps, Git timestamps, synthetic events and caller booleans cannot prove freshness.
- HASH_AGREEMENT_ONLY does not establish freshness.
- ECP checkpoint equality does not establish freshness or external authority.
- WACP integrity does not establish freshness.
- Signature verification alone does not establish replay resistance.
- Independent Witness is not claimed.

## Not yet decided

- Actual issuer identity
- Actual verifier identity and trust anchor
- Actual nonce holder/operator
- Signing algorithm and key lifecycle
- Actual trusted clock and expiry policy
- External operating environment
- Evidence schema and implementation design

## Mandatory nonclaims

- N2_EXTERNAL_BINDING_UNEXECUTED
- HER_FRESHNESS_UNPROVEN
- No authenticated freshness PASS
- No implemented external nonce ledger
- No production admission or authority
- CPython 3.11.9 PIN_PENDING
- MinGit UNRATIFIED
- Windows isolation UNVERIFIED
- FULL_INR_READY: NO

## Human freeze limit

This freeze approves only the separation of responsibilities and trust boundaries.
It does NOT approve placeholder authorities, generated signing keys, operational credentials, implementation, deployment, or promotion of any prior verdict.

N2_IMPLEMENTED:
NO

N2_EXTERNAL_BINDING_UNEXECUTED:
YES
