# RC1 repeat blind audit — recommendations

1. Introduce `BOOTSTRAP_CARGO_TARGET_DIR=/work/bootstrap-cargo-target` isolated from `/work/cargo-target`; use it only for DotSlash `cargo install`.
2. Restore `CARGO_TARGET_DIR=/work/cargo-target` before Grok Build Cargo; recheck empty target immediately before `cargo build`.
3. Extend host orchestrator to write `IMAGE_IDENTITY.txt`, `SOURCE_ACQUISITION.txt`, and host `ENVIRONMENT.txt` (optional fields as `UNKNOWN`).
4. Document preliminary vs final `EVIDENCE_MANIFEST.sha256`; require Witness regeneration after manual files finalized.
5. Strengthen `validate_witness_evidence.py` for manifest hashes and unambiguous `Witness proposed verdict:` field.
6. Prepare package version **1.0.0-rc2** (tag not created until human review); repeat blind audit after tag publish.
