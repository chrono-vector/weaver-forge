# Reproducing Weaver Forge

This guide describes reproducibility paths for Weaver Forge and separates local validation, artifact verification, build/product execution, non-formal external trials, and formal Independent Witness reproduction.

It is a documentation guide only. It does not authorize Source Weaver audit work, Independent Witness activity, release readiness, production readiness, RC9, finding closure, blocker closure, artifact regeneration, tag movement, archive or bundle mutation, or checksum changes.

For the current lifecycle boundary, see [STATUS.md](STATUS.md) and the RC8 lifecycle wording in [README.md](README.md).

---

## Current lifecycle boundary

As of the current status update:

- RC8 is an immutable static-audit candidate: `grok-build-witness-v1.0.0-rc8`.
- RC8 artifact generation and verification passed.
- That result is not a formal Source Weaver audit.
- No formal Source Weaver READY decision exists for RC8.
- No formal Source Weaver NOT READY decision exists for RC8.
- Independent Witness was not authorized.
- Independent Witness reproduction was not performed.
- C-014 remains `NOT_STARTED`.
- No finding or blocker is `CLEAR` or `CLOSED`.
- No release-readiness or production-readiness claim is made.
- RC6 and RC7 remain immutable historical NOT READY candidates.
- Existing immutable RC8 artifact bytes must not be changed.

---

## Reproduction categories

Use these categories precisely. A result in one category must not be described as a result in another category.

| Category | Meaning | Current status in this guide |
|----------|---------|------------------------------|
| Static inspection | Reading repository documents, receipts, source files, or Git metadata without executing validators, builds, product binaries, Docker, Cargo, or network-dependent commands. | Permitted as ordinary review. Does not prove validation pass, audit readiness, or independent reproduction. |
| Local receipt validation | Running `scripts/validate_receipts.py` in a full clone to check receipt structure and cited commit object existence. | Documented below as a local procedure. Not executed or revalidated by this documentation update. |
| Coverage inventory | Running `scripts/check_receipt_coverage.py` to report receipt/commit inventory and drift warnings. | Documented below as optional inventory. Mapping is not described as complete or enforceable here. |
| GitHub Actions observation | Viewing the public Actions workflow state for the repository. | Workflow existence is documented. Current CI success is not asserted by this guide. |
| RC8 artifact verification | Checking immutable RC8 artifacts, sidecars, bundles, archives, tags, checksums, or provenance records. | Lifecycle status says RC8 artifact generation and verification passed. This guide does not rerun or redefine that verification and does not authorize artifact-byte changes. |
| Build reproduction | Rebuilding software or evidence packages from documented pins. | Not authorized or specified by this general Weaver Forge guide. Follow only separately authorized package-specific instructions. |
| Product execution | Running product binaries or target software. | Not authorized by this guide. |
| Non-formal external trial reproduction | A non-authoritative outside reviewer repeats documented steps and reports observations. | Not formal Independent Witness reproduction and not a Source Weaver verdict. |
| Formal Independent Witness reproduction | A separately authorized independent witness follows an approved handoff and reports direct observations under the witness rules. | Not authorized. Not performed. C-014 remains `NOT_STARTED`. |

---

## Requirements for local receipt validation

- Git on `PATH`.
- Python 3.11 or newer.
- Full Git history for the Weaver Forge repository.

No `pip install` or virtual environment is required for the receipt validator or coverage checker documented here.

Network access is needed only to clone from GitHub or to view GitHub Actions. If you already have a full local clone, the local validation commands below do not require network access.

---

## Clone for local validation

Use a **full** clone so every cited `Commit:` hash is present locally. Shallow clones such as `git clone --depth 1 ...` may fail commit-existence checks because older cited commits may be absent.

```bash
git clone https://github.com/chrono-vector/weaver-forge.git
cd weaver-forge
```

On Linux or macOS, use `python3` if `python` is not Python 3.

To reproduce a specific repository state, check out an explicit commit or tag rather than an unpinned branch tip.

---

## Local receipt validation

From the repository root, or from `scripts/`, run:

```bash
python scripts/validate_receipts.py
```

The validator checks receipt structure and cited `Commit:` hashes. Exit code `0` means the validator passed for the local checkout; exit code `1` means at least one validation failure was found.

A successful local validator run is local validation evidence only. It is not formal Source Weaver audit evidence, not Independent Witness reproduction, not Independent Witness PASS, and not release or production readiness.

---

## Optional coverage inventory

The coverage checker reports inventory and drift information:

```bash
python scripts/check_receipt_coverage.py
```

Exit code `0` means the inventory command completed. Warnings about inventory drift may be reported and do not by themselves establish failure. The checker is not described here as enforcing complete one-to-one commit-to-receipt traceability.

---

## GitHub Actions observation

The repository contains the workflow file `.github/workflows/validate-receipts.yml`, which runs the receipt validator on push and pull request with full Git history (`fetch-depth: 0`).

To observe public workflow state, open:

```text
https://github.com/chrono-vector/weaver-forge/actions
```

Record the observed commit, workflow name, run URL, conclusion, and observation date if using Actions output as evidence.

GitHub Actions success, if observed, is CI evidence only. It is not proof of external independent reproduction, not formal Source Weaver audit evidence, not Independent Witness PASS, and not release or production readiness.

---

## RC8 artifact and provenance boundary

RC8 is identified in current status documents as:

| Item | Value |
|------|-------|
| RC8 tag | `grok-build-witness-v1.0.0-rc8` |
| RC8 annotated tag object | `8113d952d3b127d32e138dbf804141f5d1dfb26f` |
| RC8 peeled commit | `1de4b4d9523711418390f8331c95988523ef4481` |
| RC8 tree | `87b40d8a32ca536a4cdba0eee474f6171c62f6bb` |

RC8 artifact generation and verification passed according to current lifecycle authority. This guide does not recreate that process and does not authorize changes to immutable RC8 artifact bytes, archives, bundles, sidecars, checksums, fixtures, manifests, tags, commits, trees, or release identities.

---

## Witness review and external reports

External reviewers may report observations through GitHub Issues, pull requests, or another agreed channel. Reports should include:

- operating system;
- repository commit or tag;
- whether the clone was full or shallow;
- commands used;
- expected result;
- actual result;
- relevant logs;
- whether the reviewer is independent of the reviewed work.

A non-formal outside report may be useful evidence, but it must not be described as formal Independent Witness reproduction unless a separate formal handoff has been authorized.

Formal Independent Witness reproduction remains not authorized and not performed. C-014 remains `NOT_STARTED`.

---

## What local validation can support

Local validation can support claims such as:

- the local checkout contains receipt files that satisfy the validator at the time run;
- cited `Commit:` objects are present in the full local clone at the time run;
- the coverage checker completed an inventory report at the time run.

Each claim should include the command, checkout identity, date, environment, and captured output.

## What this guide does not prove

This guide does not prove:

- formal Source Weaver audit completion or a formal Source Weaver READY/NOT READY decision for RC8;
- Independent Witness authorization, reproduction, or PASS;
- C-014 completion;
- finding or blocker closure;
- release readiness;
- production readiness;
- correctness beyond the specifically observed evidence;
- bit-identical artifact reproduction;
- current CI success unless separately observed and recorded with source, commit, run URL, and date.
