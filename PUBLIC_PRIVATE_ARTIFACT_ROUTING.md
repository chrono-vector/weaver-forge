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
- the `audit_lifecycle/` product entrypoint and examples

### `PRIVATE_REPO`

A future versioned private operational repository, if and when one is created. Use for versioned operational text that should not be public:

- Owner authorization records with operational effect
- private integration notes
- internal planning that requires history
- raw internal AI reviews if retained

This document does not create that repository.

### `PRIVATE_ARTIFACT_STORE`

Private storage outside Git, if and when designated. Use for:

- real operational handoff packages
- real independent-verification completed packages
- human witness identity / signature / independence records
- transfer bundles
- build outputs
- host inventories
- raw logs
- audit-export archives
- backup / staging artifacts

This document does not create that store.

### `DO_NOT_PERSIST`

Ephemeral local logs, caches, `__pycache__/`, pytest cache, and similar generated files when retention is unnecessary.

## Explicit future prohibition

Future real operational artifacts **MUST NOT** be added to this public Weaver Forge repository by default.

| Artifact | Default destination |
|---|---|
| Real operational handoff packages | `PRIVATE_ARTIFACT_STORE` |
| Real independent-verification submissions | `PRIVATE_ARTIFACT_STORE` |
| Completed real witness packages | `PRIVATE_ARTIFACT_STORE` |
| Human / organizational witness identity and signatures | `PRIVATE_ARTIFACT_STORE` |
| Independence records | `PRIVATE_ARTIFACT_STORE` |
| Owner authorization records with operational effect | `PRIVATE_REPO` |
| Raw AI review transcripts / prompts | `PRIVATE_REPO` unless separately sanitized and deliberately published |
| Host / path inventories and operational logs | `PRIVATE_ARTIFACT_STORE` |
| Secrets / credentials | never public; do not persist in Git |

## Independent verification routing

Keep public:

- product documentation describing independence limits
- synthetic fixtures used by public tests
- evidence-preserving report guidance for uninvolved reviewers

Keep private going forward:

- completed real witness packages
- real witness submission directories
- human / org identity
- signatures
- independence records
- private witness notes
- operational intake ledgers for real runs

## Historical public material

Status: `HISTORICAL_PUBLIC_MATERIAL — FORWARD ROUTING CHANGED`

Ignore and routing rules apply **prospectively**.

Already-committed historical bytes may remain in Git history and tags.
This routing document does not rewrite Git history.

Do not pretend already-public Owner evidence disappears because of `.gitignore`.
