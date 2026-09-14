# License scope — Weaver Forge

This repository is `WEAVER_FORGE_PUBLIC_CORE`.

The Apache License, Version 2.0 in the root [`LICENSE`](LICENSE) file
applies to Owner-controlled reusable Public Core material, including:

- architecture and specifications
- schemas and contracts
- validators
- scripts and tooling
- templates
- synthetic fixtures and tests
- public reproducibility and reference documentation
- the `audit_lifecycle/` product entrypoint and examples

That grant is Apache-2.0. It is not “Apache-2.0 with extra restrictions.”
Exclusions below are **outside** the grant.

## Two-layer principle

**Public Core = Apache-2.0** for reusable public technical foundations.

**Operational / Evidence / Enterprise = Private or separately governed.**
Apache-2.0 on Public Core does not require publishing private operational
layers and does not license them.

## Excluded from the Apache-2.0 grant

The following remain publicly viewable where already committed. Public
visibility is not a license grant. Inclusion in Git history does not
relicense excluded content.

Excluded:

1. Third-party quoted or copied material, including toolchain banners,
   copyright lines, and short quotes captured in verification logs.
2. Third-party verification content, including hashes, tree listings, and
   identity facts about software the Owner does not control.
3. Human witness submissions.
4. Signatures, identity, and independence evidence.
5. Historical evidence records retained only as prior repository history.
6. Historical receipts (`receipts/**`) as committed historical records.
7. Owner operational authorization instances.
8. Content carrying another license or rights notice.

Third-party product source trees, binaries, trademarks, and upstream
LICENSE texts that are merely described or referenced are **not copied**
here and are not licensed by this repository.

Future real operational handoff packages, real independent-verification
submissions, identity/signature records, and other operational artifacts
are routed by
[`PUBLIC_PRIVATE_ARTIFACT_ROUTING.md`](PUBLIC_PRIVATE_ARTIFACT_ROUTING.md).
They must not be added here by default and are not licensed by this
Apache grant.

## Historical public material

Historical public material already committed remains in this tree and in
Git history. This license alignment does not move or delete it.

The Apache grant covers Owner-authored protocol, code, and documentation
that is wholly Owner-controlled Public Core. It does not convert recorded
third-party text, operational evidence, or mixed-rights historical
records into Owner-licensed content.

Synthetic fixtures used in public tests are Owner test material under
Apache-2.0.

## Nonclaims

```text
Public visibility ≠ license grant
Observation ≠ Interpretation
Interpretation ≠ Verification
Verification ≠ Execution
Schema-valid ≠ True
External review ≠ constitutional authority
Human/Owner authorization ≠ machine validation
```

This file does not create Evidence admission, replay authorization,
Weaver execution authorization, Independent Witness PASS, or Stage 6
authorization.

See [`NOTICE`](NOTICE) for attribution.
See [`PUBLIC_PRIVATE_ARTIFACT_ROUTING.md`](PUBLIC_PRIVATE_ARTIFACT_ROUTING.md)
for forward routing.
