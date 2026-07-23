# RC4 static blind audit — integrated non-fatal limitations

Preserved from `RC4_BATCH_4_FINAL_INTEGRATED.md` section 6 (“Integrated non-fatal limitations”). These are non-fatal limitations by originating batch. They are distinct from the 40 material blockers in `INTEGRATED_BLOCKERS.md`. None of these limitations close or downgrade any blocker.

## Batch-1 limitations

- Public discoverability is strong, but stale wording creates uncertainty.
- rc4 immutability is represented prospectively.
- `canonical_run` casing differs across files.
- Machine ceiling does not encode the entire policy.
- Rust/DotSlash override rules conflict with stricter identity wording.
- Timestamp fallback run IDs can collide.
- `HOST_RUN_METADATA.txt` has no normative schema.
- Host tests inspect source text rather than behavior.
- Golden fixtures share assumptions with their builder.
- Witness-ID behavior lacks a complete matrix.
- `WORK_ROOT` protections lack a complete behavioral matrix.
- Reset authorization lacks behavioral tests.
- symlink target survival is not behaviorally tested.
- detached package probing lacks a dedicated isolated test.
- annotated versus lightweight tags lack testing.
- Docker ordering lacks testing.
- closed inventory checks names rather than current-run origin.
- `canonical_run` vocabulary is not normalized.
- “Cannot drift” applies only within the synthetic fixture system.
- Docker metadata failures become UNKNOWN.
- tag dereference does not prove raw tag type.
- run-ID randomness is not backed by atomic creation.
- strong host controls are only textually tested.
- optional auxiliary evidence contains load-bearing unschematized data.

## Batch-2 limitations

- RepoDigest comparison uses substring matching.
- Docker inspect stderr is discarded.
- OS/architecture failures share one stage.
- image-pull logs are not semantically validated.
- apt package versions are unpinned.
- `dpkg-query` is best effort.
- apt and DotSlash detailed logs remain outside `EVIDENCE_DIR`.
- `RUSTUP_HOME` is inherited.
- broad writable `WORK_ROOT` weakens path isolation.
- evidence has multiple writable aliases.
- protoc is not semantically version-pinned.
- Cargo executes through `bash -c`.
- Rust/Cargo parsing captures only `x.y.z`.
- pre-Cargo failures generally collapse to exit 1.
- static-inspection failure preserves artifact-present outcome and relies on ceiling.
- host and container duplicate expected constants.
- network mode is bridge.
- missing `cargo_started` defaults to `NO` in host parsing.
- `BUILD_TIMING` tuple consistency is partial.
- validator outcome inference is more permissive than host authority.
- extra generated fields are accepted.
- product/`ldd` prohibition is static rather than behaviorally traced.

## Batch-3 Part-1 limitations

- pull-log presence documentation is inaccurate.
- empty directories may remain unhashed.
- special nonregular objects are not all explicitly rejected.
- manifest generation accepts names broader than validator grammar.
- post-validation immutability is procedural.
- validator-output location depends on caller discipline.
- failure-stage vocabulary is not centralized.
- status vocabularies vary.
- boolean capitalization varies.
- manifest self-integrity depends on an outer immutable object.
- synthetic fixtures do not prove actual runtime output.
- malformed pseudo-fields may be treated as prose.

## Batch-3 Part-2 limitations

- independence is self-attested.
- a Witness may propose a stricter verdict than the machine ceiling.
- “first matching row governs” wording differs from conservative lowering behavior.
- AI assistance detail is free text.
- Witness identity is not externally verified.
- failure-stage free text complicates precedence.
- redaction prohibition uses substring matching.
- permitted redactions reduce diagnostics.
- correction guarantees rely on Git history.
- historical intake needs a distinct mode.
- human justification is not semantically validated.
- manual forms are tested only through synthetic fixtures.

## Audit-method limitations (Phase 0 intake)

- This audit is **static only**. No Docker, Cargo, rustc, rustup, DotSlash, protoc, `ldd`, Witness script, validator, validator test, or product command was executed.
- This audit is **not** Independent Witness reproduction. Claim C-014 remains `NOT_STARTED`.
- This Phase 0 intake preserves findings; it does not remediate or close any of the 40 blockers.
- No Independent Witness PASS is claimed.
