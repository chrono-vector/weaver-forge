# Witness package release identity

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc4** |
| Canonical package tag | **`grok-build-witness-v1.0.0-rc4`** |
| Package commit authority | **annotated_tag_resolution** (no embedded future rc4 commit) |
| Package readiness | **NOT READY** until rc4 is committed, tagged, and repeat-audited |
| Independent Witness (C-014) | **NOT_STARTED** |
| Overall | **PARTIAL** |
| Grok Build source commit (upstream pin) | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

## Current status banner

**RC3 INTEGRATED STATIC BLIND-AUDIT RECORDED — RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT**

- `canonical_package_tag=grok-build-witness-v1.0.0-rc4`
- Tag availability is verified by annotated-tag resolution
- Canonical execution requires successful annotated-tag resolution
- If resolution fails, canonical execution stops
- After publication, the tag is immutable
- Later `main`-branch status/audit records are outside the tagged snapshot

## Immutable historical releases

| Tag | Commit | Audit performed | Audit verdict |
|-----|--------|------------------|----------------|
| `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | Repeat public-entry-point blind audit | **NOT READY** |
| `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | Integrated four-batch static blind audit | **NOT READY** |
| `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | Integrated four-batch static blind audit (preserved under `evidence/rc3-static-blind-audit/`) | **NOT READY** |

rc1, rc2, and rc3 must not be moved, deleted, or force-updated. Each remains an immutable historical release with a recorded **NOT READY** audit.

## Canonical package identity model

The **annotated package tag** is the canonical package entry identity.

Canonical rc4 execution:

1. Uses the exact tag `grok-build-witness-v1.0.0-rc4`
2. Fresh-clones Weaver Forge and fetches tags from `origin`
3. Resolves `refs/tags/grok-build-witness-v1.0.0-rc4^{commit}` to one full 40-character commit
4. Checks out that commit **detached**
5. Requires checked-out `HEAD` to equal the resolved tag commit
6. Requires the package clone to be clean
7. Records requested tag, resolved commit, HEAD, detached state, and clean state in Witness evidence
8. Uses that resolved full commit as the **run-specific** immutable Weaver Forge package identity

**Tag availability** is verified only through Git resolution of the annotated tag. Canonical execution requires that resolution to succeed. If resolution fails, canonical execution must stop with truthful failure evidence. After successful publication, the tag is immutable and its resolved full commit is the package identity for that run.

The tagged package **does not embed its own commit hash**. Embedding a self-commit would create a circular identity: editing the tree to insert the commit hash changes the commit hash.

Do **not** use floating `main` as package identity. Repeat blind audit must inspect the **rc4 tag**, not floating `main`.

An optional externally supplied expected commit (`WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT`) may be used as an **additional** verification input only. It is not required for canonical execution, must not be stored as a placeholder inside the fixed tagged package, and when supplied must match the resolved tag commit and detached HEAD or the run stops.

## Tag policy

- Canonical package tag name: **`grok-build-witness-v1.0.0-rc4`**.
- Publication and availability must be verified by resolving the annotated tag.
- After publication, the rc4 tagged tree is the **immutable package snapshot**.
- **`grok-build-witness-v1.0.0-rc1`**, **`grok-build-witness-v1.0.0-rc2`**, and **`grok-build-witness-v1.0.0-rc3`** must not be moved, deleted, or force-updated.
- **`grok-build-witness-v1.0.0-rc4` must not be moved, deleted, recreated, or force-updated** after publication. Never rewrite the tagged snapshot to insert a commit hash, amend the tagged commit, recreate the tag, or force-update it.
- The package remains **NOT READY** until rc4 is committed, tagged, and repeat-audited.

## Evidence requirements for canonical runs

Witness evidence must record:

| Field | Required |
|-------|----------|
| Package tag requested | `grok-build-witness-v1.0.0-rc4` |
| Full Weaver Forge commit **resolved from the annotated tag** | 40-char lowercase git commit |
| Detached HEAD equals resolved tag commit | yes |
| Package clone clean | yes |
| Grok Build source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Host helper `run_witness_narrow_build.sh` fails clearly if the requested tag cannot be resolved, if detached HEAD does not match the resolved tag commit, or if the package clone is dirty.

## Tagged snapshot vs later main-branch records

### A. Tagged package content

- Immutable at `grok-build-witness-v1.0.0-rc4` after successful publication of the annotated tag
- Is the object of the repeat blind audit
- Must **not** be edited after tagging to insert its own commit hash

### B. Later status / audit record on `main`

A later `main`-branch commit may record:

- the observed rc4 resolved commit (read from the published tag)
- tag publication confirmation
- repeat blind-audit result
- readiness decision

That later commit:

- is **not** part of the rc4 tagged snapshot
- must **not** alter, move, recreate, or force-update rc4
- must **not** be described as changing the contents of rc4
- must preserve all prior audit history (rc1, rc2, rc3)

### Checklist for later `main` status-only updates (if needed)

- [ ] Confirm `grok-build-witness-v1.0.0-rc4` by resolving the annotated tag on `origin` (do not rewrite the tagged tree).
- [ ] Make a dedicated status-only commit on `main` if released-state wording outside the tagged snapshot must change.
- [ ] Do not backdate or alter the rc1, rc2, or rc3 immutable history rows above.
- [ ] Do not claim package readiness (`READY`) unless a repeat blind audit against the published rc4 tag has recorded a READY verdict.
- [ ] Never rewrite the tagged snapshot to insert a commit hash, amend the tagged commit, recreate rc4, or force-update the tag.

## HISTORICAL PRE-TAG STATE

Earlier normative wording treated rc3 as the current package candidate and used phrases such as “until rc3 tag exists,” “after rc3 tag exists,” “before rc3 tag exists,” “rc3 tag pending,” or “proposed tag” as current identity. That state is superseded: rc3 was tagged at `77221a224bbd6194cfafb81f6ecb58c800e5bc13`, audited **NOT READY** (C-026; audit preserved under `evidence/rc3-static-blind-audit/`), and is now immutable history. rc4 is the current package content under preparation.
