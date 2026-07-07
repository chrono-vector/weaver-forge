# E4 Independent Reproduction Plan

## Purpose of Independent Reproduction

Independent Reproduction (E4) is the step where an uninvolved third party repeats the repository's documented validation process and records what they directly observed.

The purpose is not to prove the project is complete, correct, production-ready, or externally audited. The purpose is to prove that a reviewer who did not author the cited work can independently reproduce the current evidence trail from a clean clone using the repository's published instructions.

## Requirements for an Independent Reviewer

The reviewer must be uninvolved in the cited work.

Minimum reviewer requirements:

- No authorship on the commits being reviewed
- No claim of independence if operating as the project author or in the author's own attestation role
- Git available on `PATH`
- Python 3.11 or newer
- Network access to clone the repository and view GitHub Actions
- Willingness to record exact commands run, exact commit reviewed, and exact outcomes observed

Reviewer posture:

- Evidence-first
- Reproduce only what is actually documented
- Claim only what was directly observed
- Treat missing evidence as unproven, not implied

## Exact Reproduction Procedure

The reviewer should perform the procedure below against a specific public commit on `main`.

### 1. Record review target

Before running anything, record:

- Repository URL
- Branch reviewed
- Full commit hash reviewed
- Review date
- Reviewer name or handle
- Confirmation that the reviewer is uninvolved in the cited work

### 2. Create a full local clone

Use a full clone. Do not use `--depth 1`, because commit-existence checks require full history.

```bash
git clone https://github.com/chrono-vector/weaver-forge.git
cd weaver-forge
git rev-parse HEAD
```

Record the resulting `HEAD` commit hash.

### 3. Confirm runtime requirements

Verify Python 3.11+ is available:

```bash
python --version
```

If `python` is not Python 3 on the reviewer's platform, use the platform-appropriate Python 3 command and record that fact.

### 4. Run the receipt validator

From the repository root:

```bash
python scripts/validate_receipts.py
```

Record:

- Exit code
- One `PASS` or `FAIL` line per receipt
- Any error output

### 5. Run the receipt coverage checker

From the repository root:

```bash
python scripts/check_receipt_coverage.py
```

Record:

- Exit code
- Coverage output
- Any drift or warning messages

Warnings are evidence and should be preserved, not omitted.

### 6. Review repository state documents

Open and review:

- `STATUS.md`
- `PROJECT_METRICS.md`
- `REPRODUCE.md`
- `WITNESS_REVIEW_TEMPLATE.md`
- `E4_REPRODUCTION_PLAN.md`

Record whether these files were present and whether their claims matched the reproduced results.

### 7. Verify GitHub Actions status

Open:

[https://github.com/chrono-vector/weaver-forge/actions](https://github.com/chrono-vector/weaver-forge/actions)

Check the latest **Validate Receipts** workflow for the reviewed `main` commit.

Record:

- Workflow name
- Commit checked
- Pass/fail result
- Review timestamp

### 8. Produce a witness record

Complete `WITNESS_REVIEW_TEMPLATE.md` or an equivalent evidence-preserving report that includes:

- Reviewer identity
- Independence statement
- Commit reviewed
- Commands executed
- Outputs observed
- Failures, warnings, or deviations
- Final conclusion: `Reproduced`, `Partially reproduced`, or `Not reproduced`

## Success Criteria

The reproduction attempt is successful only if the reviewer can directly verify all of the following for the reviewed commit:

- Repository cloned successfully with full history
- Python runtime was sufficient to execute the documented commands
- `python scripts/validate_receipts.py` ran successfully and its output was recorded
- `python scripts/check_receipt_coverage.py` ran successfully and its output was recorded
- GitHub Actions status for the reviewed `main` commit was checked and recorded
- A witness record was produced by an uninvolved reviewer
- The witness record states only what was directly reproduced

## Evidence That Should Be Collected

Collect raw evidence, not just conclusions.

Required evidence:

- Repository URL
- Branch name
- Full reviewed commit hash
- Reviewer name or handle
- Independence statement
- `python --version` output
- Full validator output
- Full coverage checker output
- GitHub Actions result for the reviewed commit
- Completed witness review document

Preferred supporting evidence:

- Terminal transcript or pasted command log
- Screenshot or link for the GitHub Actions run
- Notes on any mismatch between documentation and observed behavior

## What the Reviewer Should NOT Claim

The reviewer should not claim any of the following unless separately evidenced:

- That E4 has been achieved merely because the repository appears organized
- That the project is production-ready
- That the project has passed an external audit
- That all repository claims are universally true beyond the validated scope
- That long-term consistency has been proven
- That receipt coverage is complete beyond what the tools actually report
- That reviewer attestation equals project authority

The reviewer must not claim independent reproduction if they were involved in authoring the reviewed work.

## What Constitutes Successful E4 Completion

E4 is complete only when all of the following are true:

- An uninvolved third party executed the documented reproduction procedure
- The reviewer recorded the exact commit reviewed
- The reviewer captured the validator and coverage outputs as evidence
- The reviewer checked the corresponding GitHub Actions result
- The reviewer produced a witness record with an explicit independence statement
- The witness conclusion is `Reproduced` or a clearly bounded equivalent

E4 is not complete because this plan exists. E4 is not complete because the author can rerun the commands. E4 requires execution by an uninvolved third party.

## Remaining Limitations After E4

Even after successful E4 completion, the following remain out of scope unless separately evidenced:

- External audit
- Production readiness
- Security assurance beyond present repository evidence
- Long-term operational consistency
- Completeness of all historical claim-to-commit mapping beyond current checks
- Correctness beyond the validator and documented review boundaries

Successful E4 would prove independent reproduction of the current evidence process. It would not prove everything about the project.
