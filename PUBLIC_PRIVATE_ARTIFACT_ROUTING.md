# Public / private artifact routing

This repository is intended to function as `WEAVER_FORGE_PUBLIC_CORE`.

That means:

- public protocol and reference architecture
- reusable validation tools
- synthetic and reference tests
- historical public material already committed
- not a public dump of future operational evidence

This document is a routing policy for **future** artifacts. It does **not** create a private repository, a private artifact store, or a new repo topology. Those destinations are named defaults. They are not claimed to exist yet.

`.gitignore` in this repository is **accidental-publication containment**, not access control. Ignore rules do not hide already-tracked files, do not rewrite history, and do not replace authorization.

## Authority / nonclaim

```text
Observation ≠ Interpretation
Interpretation ≠ Verification
Verification ≠ Execution
Schema-valid ≠ True
Replayable ≠ Externally True
REPLAY_ELIGIBLE_BY_CONTRACT ≠ Replay Authorized
Ingress Ready ≠ Evidence Admitted
Ingress Ready ≠ Weaver Execution Authorized
Ingress Ready ≠ Independent Witness PASS
Ingress Ready ≠ Stage 6
External review ≠ constitutional authority
Human/Owner authorization ≠ machine validation
```

Public-core containment ≠ secret protection.
Routing policy ≠ Evidence admission.
Ignore rules ≠ Independent Witness.

## Default destinations

### `PUBLIC_REPO`

This public Weaver Forge repository. Use for:

- architecture
- protocol / specification
- schemas / contracts
- pure validators
- templates
- synthetic fixtures
- public tests
- public reproducibility docs
- nonclaim / authority boundaries
- public Independent Witness protocol
- VECTOR Package Ingress v0 protocol, code, and tests

### `PRIVATE_REPO`

A future versioned private operational repository, if and when one is created. Use for versioned operational text that should not be public:

- Owner authorization records with operational effect
- private integration notes
- internal planning that requires history
- future named-person / organization GOV instances
- raw internal AI reviews if retained

W1 does not create this repository.

### `PRIVATE_ARTIFACT_STORE`

Private storage outside Git, if and when designated. Use for:

- real VECTOR handoff ZIPs
- real eight-member package bytes
- real Ingress results
- Replay results
- Verification results
- Independent Witness completed packages
- human witness identity / signature / independence records
- transfer bundles
- build outputs
- host inventories
- raw logs
- audit-export ZIPs
- backup / staging artifacts

W1 does not create this store.

### `DO_NOT_PERSIST`

Ephemeral local logs, caches, `__pycache__/`, pytest cache, and similar generated files when retention is unnecessary.

## Explicit future prohibition

Future real operational artifacts **MUST NOT** be added to this public Weaver Forge repository by default.

| Artifact | Default destination |
|---|---|
| Real VECTOR Handoff ZIPs | `PRIVATE_ARTIFACT_STORE` |
| Real VECTOR package members | `PRIVATE_ARTIFACT_STORE` |
| Real VECTOR Ingress result JSON | `PRIVATE_ARTIFACT_STORE` |
| Real Independent Witness submissions | `PRIVATE_ARTIFACT_STORE` |
| Completed real witness packages | `PRIVATE_ARTIFACT_STORE` |
| Human / organizational witness identity and signatures | `PRIVATE_ARTIFACT_STORE` |
| Independence records | `PRIVATE_ARTIFACT_STORE` |
| Owner authorization records with operational effect | `PRIVATE_REPO` |
| Raw AI review transcripts / prompts | `PRIVATE_REPO` unless separately sanitized and deliberately published |
| Host / path inventories and operational logs | `PRIVATE_ARTIFACT_STORE` |
| Secrets / credentials | never public; do not persist in Git |

`VECTOR_INGRESS_REAL_ZIP` remains optional Owner-local integration only. It is not a license to commit the ZIP or its result into this repository.

## VECTOR Ingress routing

Keep public:

- `external_verifications/vector-handoff/README.md`
- VECTOR Ingress v0 code
- schema
- synthetic tests / fixtures

Keep private going forward:

- real VECTOR ZIP
- real package members
- real package IDs / digests when tied to operational package publication
- real Ingress result JSON
- stdout captures containing owner-local paths

## Independent Witness routing

Keep public:

- runbook
- requirements
- classification
- security / redaction policy
- schemas
- templates
- validators
- synthetic fixtures
- `external_verifications/grok-build/witness-submissions/README.md` as a policy-only placeholder

Keep private going forward:

- completed real witness package
- real witness submission directory (`witness-submissions/<run_id>/`)
- human / org identity
- signatures
- independence records
- private witness notes
- operational intake ledgers for real runs

## Historical public material

Status: `HISTORICAL_PUBLIC_MATERIAL — FORWARD ROUTING CHANGED`

Ignore and routing rules apply **prospectively**.

Already-committed historical bytes remain in Git history and tags. This includes existing `external_verifications/grok-build/evidence/**`, historical receipts, GOV-002 / GOV-003 / GOV-004, existing RC8 historical records, frozen tagged bytes, owner historical notes already public, `ENVIRONMENT.md`, historical `REPRODUCTION.md`, and the current Witness protocol tree.

W1 does not remove, relocate, or rewrite that material. W1 does not rewrite Git history.

Do not pretend already-public Owner evidence disappears because of `.gitignore`.
