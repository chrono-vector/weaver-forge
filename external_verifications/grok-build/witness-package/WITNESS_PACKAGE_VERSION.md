# Witness package release identity

| Field | Value |
|-------|-------|
| Package version | **1.0.0-rc5** |
| Canonical package tag | **`grok-build-witness-v1.0.0-rc5`** |
| Package commit authority | **annotated_tag_resolution** (resolved commit is derived at tag publication / run time; this tree does **not** embed a future commit, tag-object, archive, or bundle hash) |
| Package readiness | **NOT READY** (rc5 is an immutable static-audit candidate only; rc4 static disposition remains **NOT READY** with 40 integrated blockers) |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **NONE** |
| Independent Witness (C-014) | **NOT_STARTED** |
| Candidate state | rc5 candidacy authorized; **rc5 tag, archive, and transfer bundle do not yet exist** until after Pi-conformance commit/push/tag |
| Overall | **PARTIAL** |
| Grok Build source commit (upstream pin) | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

## Current status banner

**RC5 IMMUTABLE STATIC-AUDIT CANDIDATE — NOT READY — RC4 FIXED IMMUTABLE — STATIC BLIND AUDIT COMPLETE — FINAL DISPOSITION NOT READY (40 BLOCKERS) — RC5 TAG/ARCHIVE/BUNDLE DO NOT YET EXIST — C-014 NOT_STARTED**

- `canonical_package_tag=grok-build-witness-v1.0.0-rc5`
- Tag availability is verified by annotated-tag resolution
- Canonical execution requires successful annotated-tag resolution
- If resolution fails, canonical execution stops
- After publication, the tag is immutable and must not be moved, deleted, recreated, or force-updated
- rc5 is described only as an **immutable static-audit candidate** — not READY, not Independent Witness PASS
- Later `main`-branch status/audit/remediation records outside a tagged snapshot do not alter prior immutable releases

## Immutable releases

| Version | Tag | Commit | Release state | Static audit status | Static disposition | Independent Witness reproduction | C-014 |
|---------|-----|--------|---------------|---------------------|--------------------|----------------------------------|-------|
| `1.0.0-rc1` | `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc2` | `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc3` | `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc4` | `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** | NOT_PERFORMED | NOT_STARTED |
| `1.0.0-rc5` | `grok-build-witness-v1.0.0-rc5` | *(resolved at annotated-tag publication; not embedded here)* | STATIC_AUDIT_CANDIDATE | NOT YET AUDITED AS TAGGED RELEASE | **NOT READY** (candidate only) | NOT_PERFORMED | NOT_STARTED |

rc1–rc4 must not be moved, deleted, or force-updated. No readiness PASS is assigned to any row. **rc5 tag does not yet exist** until created after Pi-conformance commit and push.

## Canonical package identity model

The **annotated package tag** is the canonical package entry identity.

Canonical rc5 execution (once the annotated tag exists):

1. Uses the exact tag `grok-build-witness-v1.0.0-rc5`
2. Fresh-clones Weaver Forge and fetches tags from `origin`
3. Resolves `refs/tags/grok-build-witness-v1.0.0-rc5^{commit}` to one full 40-character commit
4. Checks out that commit **detached**
5. Requires checked-out `HEAD` to equal the resolved tag commit
6. Requires the package clone to be clean
7. Records requested tag, resolved commit, HEAD, detached state, and clean state in Witness evidence
8. Uses that resolved full commit as the **run-specific** immutable Weaver Forge package identity

**Tag availability** is verified only through Git resolution of the annotated tag. Canonical execution requires that resolution to succeed. If resolution fails, canonical execution must stop with truthful failure evidence. After publication, the tag is immutable and its resolved full commit is the package identity for that run.

The tagged package **does not embed its own commit hash**. Embedding a self-commit would create a circular identity: editing the tree to insert the commit hash changes the commit hash.

Do **not** use floating `main` as package identity. Static audit of the fixed rc4 tag is complete (**NOT READY**). rc5 remains an immutable static-audit candidate only until a later fixed-candidate audit (or Independent Witness reproduction) records otherwise.

### Historical rc4 compatibility

Historical evidence declaring `package_version=1.0.0-rc4` continues to require tag `grok-build-witness-v1.0.0-rc4`. Tag mismatch itself must never be used to infer historical compatibility. Unknown or unsupported `package_version` values fail closed.

An optional externally supplied expected commit (`WEAVER_FORGE_EXTERNAL_EXPECTED_COMMIT`) may be used as an **additional** verification input only. It is not required for canonical execution, must not be stored as a placeholder inside the fixed tagged package, and when supplied must match the resolved tag commit and detached HEAD or the run stops.

## Tag policy

- Canonical package tag name (active candidate): **`grok-build-witness-v1.0.0-rc5`**.
- Historical fixed rc4 tag: **`grok-build-witness-v1.0.0-rc4`** → **`039b46737c5968a81fb756d7a6d1d0dd57b6ad96`** (**NOT READY**).
- Publication and availability must be verified by resolving the annotated tag.
- **`grok-build-witness-v1.0.0-rc1`**, **`grok-build-witness-v1.0.0-rc2`**, **`grok-build-witness-v1.0.0-rc3`**, and **`grok-build-witness-v1.0.0-rc4`** must not be moved, deleted, recreated, or force-updated.
- Never rewrite a tagged snapshot to insert a commit hash, amend the tagged commit, recreate the tag, or force-update it.
- The package remains **NOT READY**. rc5 is an immutable static-audit candidate only. Independent Witness reproduction **NOT PERFORMED**. C-014 **NOT_STARTED**. Overall **PARTIAL**.

## Evidence requirements for canonical runs

Witness evidence must record:

| Field | Required |
|-------|----------|
| Package tag requested | `grok-build-witness-v1.0.0-rc5` for `package_version=1.0.0-rc5` (historical `1.0.0-rc4` requires `grok-build-witness-v1.0.0-rc4`) |
| Full Weaver Forge commit **resolved from the annotated tag** | 40-char lowercase git commit |
| Detached HEAD equals resolved tag commit | yes |
| Package clone clean | yes |
| Grok Build source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Host helper `run_witness_narrow_build.sh` fails clearly if the requested tag cannot be resolved, if detached HEAD does not match the resolved tag commit, or if the package clone is dirty.

## Tagged snapshot vs later main-branch records

### A. Tagged package content (historical rc4)

- Immutable at `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`
- Was the object of the rc4 static blind audit (disposition **NOT READY**)
- Must **not** be edited after tagging to insert its own commit hash

### B. Later status / audit / remediation record on `main` (toward rc5)

A later `main`-branch commit may record:

- the observed rc4 resolved commit (read from the published tag)
- documentation/status-truthfulness and technical remediation toward the rc5 candidate
- later static re-audit or readiness decision against a future fixed candidate

That later commit:

- is **not** part of the rc4 tagged snapshot
- must **not** alter, move, recreate, or force-update rc1–rc4
- must **not** be described as changing the contents of rc4
- must preserve all prior audit history (rc1, rc2, rc3, rc4)
- must **not** claim that an rc5 tag exists until one is actually created
- must **not** claim READY, Independent Witness PASS, or C-014 completion without corresponding evidence

### Checklist for later `main` status-only updates (if needed)

- [ ] Confirm historical `grok-build-witness-v1.0.0-rc4` by resolving the annotated tag on `origin` (do not rewrite the tagged tree).
- [ ] Make a dedicated status-only commit on `main` if released-state wording outside the tagged snapshot must change.
- [ ] Do not backdate or alter the rc1, rc2, rc3, or rc4 immutable history rows above.
- [ ] Do not claim package readiness (`READY`) unless a later fixed-candidate static audit (or Independent Witness reproduction) records a READY verdict.
- [ ] Never rewrite a tagged snapshot to insert a commit hash, amend the tagged commit, recreate a historical tag, or force-update it.
- [ ] Do not create, imply, or claim an rc5 tag until one actually exists.

## HISTORICAL PRE-TAG STATE

Earlier normative wording treated rc3 as the current package candidate and used phrases such as “until rc3 tag exists,” “after rc3 tag exists,” “before rc3 tag exists,” “rc3 tag pending,” or “proposed tag” as current identity. That state is superseded: rc3 was tagged at `77221a224bbd6194cfafb81f6ecb58c800e5bc13`, audited **NOT READY** (C-026; audit preserved under `evidence/rc3-static-blind-audit/`), and is now immutable history. Separately, pre-publication wording described rc4 as “package content under preparation” / “NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT.” That prospective wording is superseded: rc4 is fixed and immutable at the identity in the table above, statically audited **NOT READY** (C-027). Current active candidate identity is **`1.0.0-rc5` / `grok-build-witness-v1.0.0-rc5`** as an immutable static-audit candidate only; **the rc5 tag does not yet exist**.
