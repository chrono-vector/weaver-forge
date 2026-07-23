# Witness package release identity

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc4** |
| Canonical package tag | **`grok-build-witness-v1.0.0-rc4`** |
| Fixed tagged commit | **`039b46737c5968a81fb756d7a6d1d0dd57b6ad96`** |
| Package commit authority | **annotated_tag_resolution** (resolved commit is the fixed rc4 release identity) |
| Package readiness | **NOT READY** (rc4 static disposition; 40 integrated blockers remain) |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **NONE** |
| Independent Witness (C-014) | **NOT_STARTED** |
| Successor state | Phase 1 documentation remediation on `main`; technical implementation remediation NOT YET BEGUN; `main` prepared toward possible future rc5 candidate; **rc5 tag does not exist** |
| Overall | **PARTIAL** |
| Grok Build source commit (upstream pin) | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

## Current status banner

**RC4 FIXED IMMUTABLE — STATIC BLIND AUDIT COMPLETE — FINAL DISPOSITION NOT READY (40 BLOCKERS) — PHASE 1 DOCUMENTATION REMEDIATION ON MAIN — TECHNICAL IMPLEMENTATION REMEDIATION NOT YET BEGUN — RC5 TAG DOES NOT EXIST — C-014 NOT_STARTED**

- `canonical_package_tag=grok-build-witness-v1.0.0-rc4`
- Fixed tagged commit: `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`
- Tag availability is verified by annotated-tag resolution
- Canonical execution requires successful annotated-tag resolution
- If resolution fails, canonical execution stops
- The tag is immutable and must not be moved, deleted, recreated, or force-updated
- Later `main`-branch status/audit/remediation records are outside the tagged snapshot
- Phase 0 audit intake is complete; Phase 1 documentation and release/status remediation is being performed on `main`; technical implementation remediation of scripts, schemas, validators, tests, and execution controls has not begun

## Immutable releases

| Version | Tag | Commit | Release state | Static audit status | Static disposition | Independent Witness reproduction | C-014 |
|---------|-----|--------|---------------|---------------------|--------------------|----------------------------------|-------|
| `1.0.0-rc1` | `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc2` | `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc3` | `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc4` | `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |

rc1–rc4 must not be moved, deleted, or force-updated. No readiness PASS is assigned to any row. **rc5 tag does not exist.**

## Canonical package identity model

The **annotated package tag** is the canonical package entry identity.

Canonical rc4 execution:

1. Uses the exact tag `grok-build-witness-v1.0.0-rc4`
2. Fresh-clones Weaver Forge and fetches tags from `origin`
3. Resolves `refs/tags/grok-build-witness-v1.0.0-rc4^{commit}` to one full 40-character commit (`039b46737c5968a81fb756d7a6d1d0dd57b6ad96`)
4. Checks out that commit **detached**
5. Requires checked-out `HEAD` to equal the resolved tag commit
6. Requires the package clone to be clean
7. Records requested tag, resolved commit, HEAD, detached state, and clean state in Witness evidence
8. Uses that resolved full commit as the **run-specific** immutable Weaver Forge package identity

**Tag availability** is verified only through Git resolution of the annotated tag. Canonical execution requires that resolution to succeed. If resolution fails, canonical execution must stop with truthful failure evidence. The tag is immutable and its resolved full commit is the package identity for that run.

The tagged package **does not embed its own commit hash**. Embedding a self-commit would create a circular identity: editing the tree to insert the commit hash changes the commit hash.

Do **not** use floating `main` as package identity. Static audit of the fixed rc4 tag is complete (**NOT READY**). Phase 1 documentation remediation is being performed on `main`; technical implementation remediation has not begun; that work is outside the immutable rc4 snapshot.

An optional externally supplied expected commit (`WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT`) may be used as an **additional** verification input only. It is not required for canonical execution, must not be stored as a placeholder inside the fixed tagged package, and when supplied must match the resolved tag commit and detached HEAD or the run stops.

## Tag policy

- Canonical package tag name: **`grok-build-witness-v1.0.0-rc4`**.
- Fixed tagged commit: **`039b46737c5968a81fb756d7a6d1d0dd57b6ad96`**.
- Publication and availability must be verified by resolving the annotated tag.
- The rc4 tagged tree is the **immutable package snapshot**.
- **`grok-build-witness-v1.0.0-rc1`**, **`grok-build-witness-v1.0.0-rc2`**, **`grok-build-witness-v1.0.0-rc3`**, and **`grok-build-witness-v1.0.0-rc4`** must not be moved, deleted, recreated, or force-updated.
- Never rewrite the tagged snapshot to insert a commit hash, amend the tagged commit, recreate the tag, or force-update it.
- The package remains **NOT READY** (rc4 static disposition). Phase 0 audit intake is complete. Phase 1 documentation and release/status remediation is being performed on `main`. Technical implementation remediation of scripts, schemas, validators, tests, and execution controls has not begun. `main` is being prepared toward a possible future rc5 candidate; **no rc5 tag exists**.

## Evidence requirements for canonical runs

Witness evidence must record:

| Field | Required |
|-------|----------|
| Package tag requested | `grok-build-witness-v1.0.0-rc4` |
| Full Weaver Forge commit **resolved from the annotated tag** | 40-char lowercase git commit (`039b46737c5968a81fb756d7a6d1d0dd57b6ad96`) |
| Detached HEAD equals resolved tag commit | yes |
| Package clone clean | yes |
| Grok Build source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Host helper `run_witness_narrow_build.sh` fails clearly if the requested tag cannot be resolved, if detached HEAD does not match the resolved tag commit, or if the package clone is dirty.

## Tagged snapshot vs later main-branch records

### A. Tagged package content

- Immutable at `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`
- Was the object of the rc4 static blind audit (disposition **NOT READY**)
- Must **not** be edited after tagging to insert its own commit hash

### B. Later status / audit / remediation record on `main`

A later `main`-branch commit may record:

- the observed rc4 resolved commit (read from the published tag)
- documentation/status-truthfulness remediation (Phase 1)
- later technical implementation remediation (scripts/schemas/validators/tests/execution controls) toward a possible future candidate — **not yet begun**
- later static re-audit or readiness decision against a future fixed candidate

That later commit:

- is **not** part of the rc4 tagged snapshot
- must **not** alter, move, recreate, or force-update rc4
- must **not** be described as changing the contents of rc4
- must preserve all prior audit history (rc1, rc2, rc3, rc4)
- must **not** claim that an rc5 tag exists until one is actually created

### Checklist for later `main` status-only updates (if needed)

- [ ] Confirm `grok-build-witness-v1.0.0-rc4` by resolving the annotated tag on `origin` (do not rewrite the tagged tree).
- [ ] Make a dedicated status-only commit on `main` if released-state wording outside the tagged snapshot must change.
- [ ] Do not backdate or alter the rc1, rc2, rc3, or rc4 immutable history rows above.
- [ ] Do not claim package readiness (`READY`) unless a later fixed-candidate static audit (or Independent Witness reproduction) records a READY verdict.
- [ ] Never rewrite the tagged snapshot to insert a commit hash, amend the tagged commit, recreate rc4, or force-update the tag.
- [ ] Do not create, imply, or claim an rc5 tag until one actually exists.

## HISTORICAL PRE-TAG STATE

Earlier normative wording treated rc3 as the current package candidate and used phrases such as “until rc3 tag exists,” “after rc3 tag exists,” “before rc3 tag exists,” “rc3 tag pending,” or “proposed tag” as current identity. That state is superseded: rc3 was tagged at `77221a224bbd6194cfafb81f6ecb58c800e5bc13`, audited **NOT READY** (C-026; audit preserved under `evidence/rc3-static-blind-audit/`), and is now immutable history. Separately, pre-publication wording described rc4 as “package content under preparation” / “NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT.” That prospective wording is superseded: rc4 is fixed and immutable at the identity in the table above, statically audited **NOT READY** (C-027). Phase 0 audit intake is complete. Phase 1 documentation and release/status remediation is being performed on `main`. Technical implementation remediation of scripts, schemas, validators, tests, and execution controls has not begun. `main` is being prepared toward a possible future rc5 candidate; **no rc5 tag exists**.
