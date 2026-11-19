# ASIN-HHC Ledger 789 — Evidence Record 004: Run #2 archive authenticated

**Review date:** 2026-11-19 JST
**Scope:** Run evidence bundle integrity, GitHub-side artifact linkage, bounded hash replay and tamper-control log
**Verdict:** **ARCHIVE_AUTHENTICITY_PASS / MANIFEST_PASS / BOUNDED_REPLAY_PASS / NEGATIVE_CONTROL_PASS**. This is **not** proof of the real-world ledger events or a formally accredited Independent Witness.

## Exact provenance

- Reviewing repo: `chrono-vector/weaver-forge`
- Development branch: `development/independent-verification-v2`
- Workflow source commit: `36ef5cdada0209d343f0380866c57b40b27e1408`
- Run ID: **44471299765**
- Run page: https://github.com/chrono-vector/weaver-forge/actions/runs/44471299765
- Replay job ID: **135381160898**; GitHub connector reports `completed/success`.
- Archive job ID: **135381219549**; GitHub connector reports `completed/success`.
- External source: `dbottrader/ASIN-HHC-Agent-Mesh@a9b0787078dc9db9d33eac272a2c005c165acef4`
- GitHub artifact ID: **14504377731**; name: `asin-hhc-ledger-789-run-evidence`
- GitHub artifact expiry: **2027-02-17 06:19:18 UTC** (metadata at time of review; subject to platform deletion/retention behavior).
- GitHub artifact metadata digest: `sha256:7281012265988e105f14b916a993a6a724aa9dd6c32b42eebbd5007cda910670`
- Owner-uploaded ZIP filename: `asin-hhc-ledger-789-run-evidence.zip`
- ZIP bytes: **6269**; SHA-256: `7281012265988e105f14b916a993a6a724aa9dd6c32b42eebbd5007cda910670`
- The uploaded ZIP and GitHub's artifact have **matching size and SHA-256 digest**. The artifact's run metadata matches the SHA and run ID above.

## ZIP contents and independently checked hashes

The uploaded ZIP passed CRC integrity checks and contained exactly these three entries.

| Original entry | Bytes | Independently computed SHA-256 |
| --- | ---: | --- |
| `RUN_METADATA.txt` | 186 | `0e275c1f4f1d3fdef0f5d11b87312677c5869ee1f68ed31610f6e277a5a00698` |
| `independently-replay-ledger.log` | 17726 | `5e5e80cd45698dcb77510b07c887f7faf3d1c1536bc14c1c776c7563ab840ed6` |
| `asin-hhc-ledger-789-replay-output.zip` | 389 | `04d07cc79220556478f66636a70dd3aed5fc2f7c7bf63584713ce3674370ea25` |

The bundle also contains `SHA256SUMS.txt` (285 bytes, self-hash `05135ec26103e1417088de753d5b6edc82965aacf7d4cdc5e1fa299c2312886d`). All **3/3** manifest entries independently verified. The manifest does not list itself.

The nested ZIP also passed CRC checks and contained exactly one `asin-replay-output.txt` (377 bytes), SHA-256 `eb7fc249f46f39838adf9136690a2799ab3212c2b4241700fa0f4a32bd34401e`. This agrees with the earlier evidence receipt's extracted stdout digest. Note that the ZIP container SHA differs from the earlier run's ZIP container SHA (a new artifact package), while the extracted stdout bytes are identical.

## Live job-log evidence from uploaded original

`RUN_METADATA.txt` states:
```text
run=44471299765
sha=36ef5cdada0209d343f0380866c57b40b27e1408
source_repo=dbottrader/ASIN-HHC-Agent-Mesh
source_commit=a9b0787078dc9db9d33eac272a2c005c165acef4
replay_job_outcome=success
```

From `independently-replay-ledger.log`, actual logged outputs (not merely shell command text):

```text
65cd7a56213b5bf6d729168b6ce71fea1d294122f570248db2843b84e8612276  artifacts/ledger-789-replay/ledger-789.json
rows=789
tip=7ff43e4de6bb8cd1fa68c9514af4876741a1aa203377cc4fbec40c179aabefcb
expected_tip=7ff43e4de6bb8cd1fa68c9514af4876741a1aa203377cc4fbec40c179aabefcb
result=PASS
label=SELF-CHECK
NEGATIVE_CONTROL=PASS (tamper detected at seq 101)
```

`##[error]` is absent in the reviewed log. The successful conclusion of both jobs was independently fetched from GitHub's job metadata.

## Boundaries and preservation

- The log output shows the replay script's declared `SELF-CHECK` label; the different-host CI replay with exact input commit and negative control establishes a **bounded technical verification**, not human attestation or full operational qualification.
- Nothing here proves real-life performance of 789 purported activities or authenticity of ledger entry origins.
- The original ZIP is currently available as a user-provided upload and GitHub Actions artifact. **This report archives hashes and provenance, not the binary ZIP or full log in Git history.** Before expiry, retain a separately controlled original copy and verify the digest.
- Historical RC8, `main`, Ryan's earlier 15/15 report and its independence/transcript SHA questions remain unchanged.
- Do not replace evidence records 001–003; this record adds stronger direct evidence and closes their missing job-log/run-ID checks for **run #2**, not run #1.

## Follow-up

Treat the run #2 evidence collection as complete for its narrow declared scope. For durable retention beyond Actions expiry, use an access-controlled evidence store with immutable bytes, a separate manifest, and restore/hash verification. Avoid uploading raw job logs to a public repo without a privacy/secret review.
