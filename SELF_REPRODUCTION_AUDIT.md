# Self-Reproduction Audit

Blind self-reproduction audit performed 2026-07-12. This document records what was directly observed when following [REPRODUCE.md](REPRODUCE.md) from a fresh clone, without relying on undocumented knowledge.

**Audit type:** Author self-reproduction (not independent witness review).

**E4 status:** Not claimed. This audit does not satisfy E4, which requires an uninvolved third party per [E4_REPRODUCTION_PLAN.md](E4_REPRODUCTION_PLAN.md).

---

## Environment

| Item | Value |
|------|-------|
| Audit date | 2026-07-12 |
| OS | Windows 10 (build 26200) |
| Shell | PowerShell |
| Git | 2.53.0.windows.3 |
| Python | 3.14.3 (`python` on PATH) |
| Clone location | `c:\dev\weaver-forge-blind-audit` (separate from working copy) |
| Clone type | Full clone (default `git clone`, no `--depth`) |
| Repository URL | https://github.com/chrono-vector/weaver-forge |
| Branch | `main` |
| HEAD at audit time | `de4286c2d0d1f5698a445bbdca08f99f4af591e5` |
| HEAD message | `docs: add E4 independent reproduction plan` |

---

## Steps Performed

Steps follow [REPRODUCE.md](REPRODUCE.md) in order. Commands not listed in REPRODUCE.md are marked *(extra)*.

### 1. Requirements check *(extra — not explicitly listed as a step in REPRODUCE.md)*

```powershell
python --version
git --version
```

### 2. Clone

```powershell
git clone https://github.com/chrono-vector/weaver-forge.git c:\dev\weaver-forge-blind-audit
cd c:\dev\weaver-forge-blind-audit
```

Clone succeeded. Full history present (26 commits on HEAD per coverage checker).

### 3. Run the Validator

From repository root:

```powershell
python scripts/validate_receipts.py
```

Also tested from `scripts/` as permitted by REPRODUCE.md:

```powershell
cd scripts
python validate_receipts.py
```

Both invocations succeeded.

### 4. Run the Coverage Checker

Optional step per REPRODUCE.md:

```powershell
python scripts/check_receipt_coverage.py
```

### 5. GitHub Actions

REPRODUCE.md instructs opening https://github.com/chrono-vector/weaver-forge/actions in a browser. `gh` CLI was not available in this environment. Verified via GitHub REST API *(not documented in REPRODUCE.md)*:

```
GET https://api.github.com/repos/chrono-vector/weaver-forge/actions/workflows/validate-receipts.yml/runs?per_page=3
```

### 6. Expected Evidence review

Opened and compared:

- `STATUS.md`
- `PROJECT_METRICS.md`

### 7. Shallow-clone negative test *(extra — validates REPRODUCE.md warning)*

```powershell
git clone --depth 1 https://github.com/chrono-vector/weaver-forge.git c:\dev\weaver-forge-shallow-test
cd c:\dev\weaver-forge-shallow-test
python scripts/validate_receipts.py
```

Validator failed on all 12 receipts with `commit not in git`, exit code 1. Confirms REPRODUCE.md shallow-clone warning.

---

## Validation Results

### Receipt validator (full clone, repository root)

Exit code: **0**

```
PASS 2026-06-30-daily-receipt-001.md
PASS 2026-06-30-first-launch.md
PASS 2026-06-30-first-witness-review.md
PASS 2026-06-30-initial-baseline.md
PASS 2026-06-30-receipt-hash-fixes.md
PASS 2026-06-30-validator-artifact.md
PASS 2026-06-30-validator-commit-existence.md
PASS 2026-07-01-daily-receipt-002.md
PASS 2026-07-02-daily-receipt-003.md
PASS 2026-07-03-daily-receipt-004.md
PASS 2026-07-04-daily-receipt-005.md
PASS 2026-07-05-daily-receipt-006.md
```

12 receipts, 12 PASS lines. Matches one `PASS` line per file in `receipts/`.

### Receipt validator (full clone, from `scripts/`)

Exit code: **0** — identical 12 PASS lines.

### Receipt coverage checker

Exit code: **0**

```
Receipt Coverage Checker
========================
Total commits:              26
Total receipt files:        12
Latest commit (HEAD):       de4286c docs: add E4 independent reproduction plan
Latest receipt file:        2026-07-05-daily-receipt-006.md
Latest receipt binding:     b5f855e (2026-07-05-daily-receipt-006.md)
Coverage status:            not yet enforceable

Warnings:
WARN Inventory drift: 26 commits on HEAD vs 12 receipt files (exact one-to-one mapping not yet enforceable)
WARN HEAD (de4286c) is newer than the latest receipt binding commit (b5f855e in 2026-07-05-daily-receipt-006.md)
WARN 4 commit(s) on HEAD since the latest receipt binding commit (no receipt required for each commit; mapping not yet enforceable)
```

Warnings present as documented. Exit code 0 despite warnings, as REPRODUCE.md states.

### Shallow clone validator (negative test)

Exit code: **1** — all 12 receipts FAIL with `commit not in git`.

### GitHub Actions

Latest **Validate Receipts** workflow for HEAD commit `de4286c`:

| Field | Value |
|-------|-------|
| Workflow | Validate Receipts |
| Run number | 18 |
| Commit | `de4286c2d0d1f5698a445bbdca08f99f4af591e5` |
| Conclusion | success |
| URL | https://github.com/chrono-vector/weaver-forge/actions/runs/28849169971 |

---

## Problems Encountered

### Points requiring knowledge beyond REPRODUCE.md

| # | Issue | Impact |
|---|-------|--------|
| 1 | **No step to record HEAD commit hash.** REPRODUCE.md does not instruct `git rev-parse HEAD`. Reviewers must decide independently what commit they reproduced. E4_REPRODUCTION_PLAN.md includes this step; REPRODUCE.md does not. | Medium — reproducibility evidence incomplete without manual addition |
| 2 | **GitHub Actions verification is browser-only.** No CLI or API alternative documented. Reviewers without a browser or with restricted network must improvise. | Low–Medium |
| 3 | **`STATUS.md` / `PROJECT_METRICS.md` validation is undefined.** REPRODUCE.md says they "reflect the current project state" but provides no check procedure or expected values. | Medium — reviewer cannot confirm this claim mechanically |
| 4 | **Expected receipt count not stated.** Validator output gives 12 PASS lines; PROJECT_METRICS.md claims "10 files in `receipts/`". A reviewer following REPRODUCE.md alone has no baseline count. | Medium — stale metrics undetectable from REPRODUCE.md alone |
| 5 | **E4_REPRODUCTION_PLAN.md exists but is not linked from REPRODUCE.md.** A reviewer using only REPRODUCE.md misses the fuller procedure (record reviewer identity, independence statement, witness template). | Low — REPRODUCE.md is sufficient for local validation only |
| 6 | **Coverage checker marked optional in REPRODUCE.md, required in E4_REPRODUCTION_PLAN.md.** Inconsistent priority between documents. | Low |
| 7 | **PROJECT_METRICS.md stale counts.** At HEAD `de4286c`: receipts = 12 (not 10); workflow runs = 18 total (not "5 workflow runs on main"). STATUS.md dated 2026-07-05; HEAD is 2026-07-07. | Medium — contradicts "reflects current project state" |
| 8 | **"Daily Receipts 001–006" vs 12 total receipt files.** Six files are non-daily receipts (launch, baseline, validator, witness, hash-fixes). REPRODUCE.md correctly says "one PASS line per file in `receipts/`" but external summaries may confuse reviewers. | Low |
| 9 | **Windows `python` vs `python3` note.** REPRODUCE.md mentions `python3` for Linux/macOS only. On this Windows host `python` worked. No issue encountered, but no Windows-specific confirmation either. | None observed |

### Unclear wording

- **"reflects the current project state"** (Expected Evidence section) — no definition of "current" or how to verify alignment.
- **"Optional inventory report"** — unclear whether skipping it still satisfies reproduction; E4 plan treats it as required.

### Missing prerequisites

- None blocking local reproduction. Git and Python 3.11+ were sufficient.
- Network required for clone and GitHub Actions check (documented).

### Unnecessary steps

- None identified in REPRODUCE.md itself. The procedure is minimal.
- Running from both repository root and `scripts/` is permitted but redundant; one location suffices.

### Missing validation output

- REPRODUCE.md does not show example validator or coverage checker output. A first-time reviewer cannot tell whether their output is correct without reading source or receipts.
- No guidance on interpreting coverage checker warnings beyond "expected."

### Potential blockers for an independent reviewer

| Blocker | Severity | Notes |
|---------|----------|-------|
| Shallow clone | High if ignored | Documented; confirmed by negative test |
| Stale STATUS.md / PROJECT_METRICS.md | Medium | May cause false "reproduction failed" if reviewer treats metrics as ground truth |
| No witness identity / independence workflow in REPRODUCE.md | Medium for E4 | Local reproduction succeeds; E4 witness record requires separate template |
| Browser-only CI check | Low | Public API works but is undocumented |

---

## Improvements Made

| Change | Rationale |
|--------|-----------|
| Created `SELF_REPRODUCTION_AUDIT.md` | Records this audit as evidence |

No changes made to REPRODUCE.md, STATUS.md, PROJECT_METRICS.md, or tooling. Stale metrics and documentation gaps are recorded here for follow-up rather than corrected during this audit.

### Recommended improvements (not applied)

1. Update PROJECT_METRICS.md receipt count (12) and workflow run count (18+).
2. Update STATUS.md snapshot date to match latest HEAD or add "as of commit" reference.
3. Add `git rev-parse HEAD` to REPRODUCE.md clone section.
4. Add example validator and coverage checker output to REPRODUCE.md.
5. Link REPRODUCE.md to E4_REPRODUCTION_PLAN.md and WITNESS_REVIEW_TEMPLATE.md for reviewers pursuing E4.
6. Clarify how to verify STATUS.md and PROJECT_METRICS.md (or remove from Expected Evidence if not mechanically verifiable).
7. Document optional GitHub API endpoint for headless CI verification.

---

## Remaining Risks

1. **This is not E4.** The auditor is the project author environment, not an uninvolved third party. Local validation reproduces; independent witness attestation does not exist yet.

2. **Stale state documents.** STATUS.md and PROJECT_METRICS.md lag HEAD by at least two commits and undercount receipts and workflow runs. A reviewer comparing documents to observed output may conclude reproduction partially failed.

3. **Metrics drift is expected but confusing.** Coverage checker warns that HEAD outpaces latest receipt binding. This is documented behavior but may alarm reviewers unfamiliar with the "not yet enforceable" model.

4. **Shallow clone failure mode.** Correctly documented; failure is total (all receipts FAIL), not partial. Reviewers using `--depth 1` will not get a useful subset of passes.

5. **GitHub Actions evidence is out-of-band.** REPRODUCE.md requires a browser visit. Screenshot or URL capture is not specified, weakening evidence preservation.

6. **Commit existence ≠ claim truth.** Validator confirms structure and local commit object presence only. Receipt prose claims are not independently verified.

7. **No daily receipt for Day 7+ work.** Four commits since latest receipt binding (`b5f855e`). Inventory drift warnings reflect this; not a validation failure but an evidence gap.

---

## Conclusion

**Local reproduction: succeeded.**

From a fresh full clone of public `main` at `de4286c`, following REPRODUCE.md exactly:

- Receipt validator: 12/12 PASS, exit 0
- Coverage checker: exit 0 with expected drift warnings
- GitHub Actions: Validate Receipts succeeded for HEAD commit
- Shallow clone: fails as documented

**Independent reproduction (E4): not achieved.** This audit was performed by the author toolchain, not an uninvolved witness. E4 remains pending per STATUS.md and E4_REPRODUCTION_PLAN.md.

**Documentation readiness:** REPRODUCE.md is sufficient for local validation reproduction. Gaps in state-document verification, expected output examples, and CI check alternatives may slow or confuse independent reviewers but did not block this audit.
