# Security Policy

## Reporting a vulnerability

If you believe you found a security issue in Weaver Forge (the `audit_lifecycle` product or related public tooling):

1. Open a **private** GitHub Security Advisory on this repository when available, or
2. Open a GitHub Issue **without** attaching secrets, private evidence, credentials, or personal data.

Include: OS, commit/tag, exact commands, expected vs actual behavior, and sanitized logs.

Do not publish exploit proofs that mutate third-party systems. Prefer minimal, local, synthetic reproduction.

## Evidence integrity model

- Audit packages bind contents with SHA-256 inventories (`SHA256SUMS.txt` and related manifests).
- Integrity binding is **not** external notarization or a trusted timestamping service.
- Operators remain responsible for custody of private evidence outside this repository.

## Freeze immutability

- A successful freeze produces a one-shot frozen package under the run directory.
- Regenerating or overwriting an existing freeze must fail closed (`FREEZE_ALREADY_EXISTS`).
- Treat frozen packages as immutable evidence containers.

## Semantic verification

- `verify` checks hash bindings **and** registered semantic recomputation for supported adapters.
- Stored `PASS` / promoted classifications must not be trusted blindly when semantic fields disagree with recomputation.
- Unsupported claim adapters must fail conservatively (no silent semantic PASS).

## Protected / private material

- Do not commit protected or private evidence trees, owner-local absolute paths, secrets, API keys, tokens, or credentials.
- Audit examples in this repository must use synthetic data and relative paths only.
- Accidental inclusion of private evidence is a publication defect; remove it from the public surface without mutating private originals elsewhere.
