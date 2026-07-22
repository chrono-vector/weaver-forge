# Witness submission — Grok Build (1.0.0-rc4)

## Run ID

```text
<github-user-or-witness-id>-<UTC-YYYYMMDD>-<short-run-id>
```

Example: `alice-20260722-a1b2c3`

Host helper generates this automatically. `<github-user-or-witness-id>` must satisfy the
`WITNESS_ID` grammar `^[a-z0-9][a-z0-9._-]{0,63}$` (see [WITNESS_RUNBOOK.md](WITNESS_RUNBOOK.md)).

## Primary method (preferred)

1. Fork `https://github.com/chrono-vector/weaver-forge`.
2. Branch: `independent-witness/<run-id>`
3. Evidence directory:

```text
external_verifications/grok-build/witness-submissions/<run-id>/
```

4. Pull request title:

```text
Independent Grok Build Witness: <run-id>
```

5. PR description **must** include every field below (all mandatory; none may be omitted even if
   the value is a failure/negative outcome):

| Field | Required |
|-------|----------|
| Run ID | `<run-id>` exactly as recorded in the evidence directory name and every evidence file |
| Witness ID | The `witness_id` value used for this run (satisfies the `WITNESS_ID` grammar) |
| Package tag | e.g. `grok-build-witness-v1.0.0-rc4` |
| Resolved Weaver Forge commit | 40-char commit resolved from the requested tag |
| Grok Build source commit | Observed, 40-char (expected `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`) |
| Rust image digest | Observed `sha256:...` from `docker inspect` / `IMAGE_IDENTITY.txt` (expected `sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e`) |
| Outcome | One of `BUILD_NOT_STARTED` \| `CARGO_FAILED` \| `CARGO_SUCCEEDED_ARTIFACT_MISSING` \| `CARGO_SUCCEEDED_ARTIFACT_PRESENT` \| `INFRASTRUCTURE_FAILURE`, exactly as recorded in `BUILD_EXIT_CODE.txt` |
| Proposed Witness verdict | Single selected line in `WITNESS_VERDICT.md`: `Witness proposed verdict: PASS\|PARTIAL\|FAIL\|INDETERMINATE` |
| `product_executed` | `NO` |
| `ldd_used` | `NO` |
| Deviations state | `NONE` or `PRESENT`; if `PRESENT`, summarize each deviation's severity and verdict ceiling, or point precisely to `DEVIATIONS.txt` |
| Redactions state | `NONE` or `PRESENT`; if `PRESENT`, summarize each redaction's file/field/reason, or point precisely to `REDACTIONS.md` |
| Correction ledger entry (if applicable) | If this PR is a correction to a prior submission, the exact `CL-XXXX` entry ID in [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md) |

A truthful negative-outcome PR (outcome other than `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, or a
proposed verdict other than `PASS`) is a **complete, acceptable, and welcome** submission when all
required fields above are present and accurate. Omitting or softening any required field to make
a submission look more favorable is itself a redaction-policy violation (see
[WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md)).

## Required files (minimum)

- `EVIDENCE_MANIFEST.sha256`
- `WEAVER_FORGE_PACKAGE_IDENTITY.txt`
- `SOURCE_IDENTITY.txt`
- `SOURCE_ACQUISITION.txt`
- `IMAGE_IDENTITY.txt`
- `ENVIRONMENT.txt`
- Full set per [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md)
- `REDACTIONS.md`

Run structural validator (output captured **outside** the evidence directory):

```bash
python external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py \
  external_verifications/grok-build/witness-submissions/<run-id>/
```

Structural PASS does not prove execution, independence, or truthfulness.

## Final evidence manifest

After all mandatory files (including `WITNESS_STATEMENT.md`, `WITNESS_VERDICT.md`,
`DEVIATIONS.txt`, `REDACTIONS.md`) are complete, regenerate:

```bash
cd external_verifications/grok-build/witness-submissions/<run-id> && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
```

Do not include `EVIDENCE_MANIFEST.sha256` in its own hash list. Re-run the structural validator
against the final manifest, again capturing its output outside the evidence directory.

## Maintainer intake

Every submission is reviewed by a maintainer per
[MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md) and receives one of `PENDING`,
`ACCEPTED`, `REJECTED`, `CORRECTION_REQUESTED`, `DISPUTED`, or (as a post-acceptance history
annotation after ledgered supersession) `SUPERSEDED`. This intake value is recorded
**separately** from the Witness's own proposed verdict — `WITNESS_VERDICT.md`'s
`maintainer_intake_verdict` field must read `pending` at submission time; it is updated by the
maintainer in a follow-up commit, never by editing the Witness's original submission.

Current package identity: version `1.0.0-rc4`; canonical tag `grok-build-witness-v1.0.0-rc4`;
package remains **NOT READY** until rc4 is committed, tagged, and repeat-audited; C-014
**NOT_STARTED**; overall **PARTIAL**; no Independent Witness reproduction.

## Corrections policy

- Preserve original commits; **append** corrections as new commits/PRs referencing an entry in
  [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md) — never edit or force-push over the original.
- The correction ledger entry format requires: original commit, original evidence manifest
  SHA-256, correction commit, corrected manifest SHA-256, reason, affected files, and
  supersession relationship (`ADDENDUM` \| `CLARIFICATION` \| `PARTIAL_SUPERSESSION` \|
  `FULL_SUPERSESSION`). See [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md) for the full template.
- Do **not** silently erase failed runs or negative evidence. `original_negative_evidence_preserved=yes`
  is mandatory on every correction ledger entry.
- Accepted public evidence becomes **immutable historical evidence** (subsequent corrections
  reference it by commit and manifest hash; they never modify it in place).

## Fallback archive

1. ZIP/tar the evidence directory.
2. Record archive SHA-256 **before** extraction on the receiving side.
3. Private delivery is **not** public independent verification until published in the repository
   with auditable history.

## Must not modify

- Owner historical `evidence/` trees
- Pinned Grok Build source or `Cargo.lock` in upstream clone used as evidence
- Owner claim IDs (add Witness claims separately)
- Any previously accepted submission's evidence files or manifest (corrections append per
  [CORRECTION_LEDGER.md](CORRECTION_LEDGER.md) instead)

## Bit-identical note

Witness PASS does **not** require matching owner artifact SHA-256 values.

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc2 | Prior run-ID, primary-method, required-files, final-manifest, corrections, fallback-archive, and must-not-modify sections |
| 1.0.0-rc3 | Expanded mandatory PR description field table (run ID, Witness ID, package tag, resolved Weaver Forge commit, Grok Build commit, Rust image digest, proposed verdict, outcome, `product_executed`, `ldd_used`, deviations state, redactions state, correction ledger entry); added maintainer-intake section distinguishing Witness verdict from intake value; linked corrections policy to the new `CORRECTION_LEDGER.md` format |
| 1.0.0-rc4 | Status/identity advanced to `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4`; intake states aligned with SUPERSEDED; package remains NOT READY; C-014 NOT_STARTED |
