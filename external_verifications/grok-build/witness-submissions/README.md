# Witness submissions sidecars (RC6-R6 / R6-I2)

Per-run append-only maintainer intake and correction sidecars live here:

```text
external_verifications/grok-build/witness-submissions/<run_id>/MAINTAINER_INTAKE_LEDGER.txt
external_verifications/grok-build/witness-submissions/<run_id>/CORRECTION_LEDGER_ENTRIES.txt
```

These files are **outside** the hashed Witness evidence package. They must never
be listed in `EVIDENCE_MANIFEST.sha256` and must never mutate, repair, rewrite,
or reinterpret the original submitted package or `WITNESS_VERDICT.md`.

Submitted packages keep `maintainer_intake_verdict=pending` forever. Later
dispositions append to `MAINTAINER_INTAKE_LEDGER.txt` only.

Corrections that would change integrity-critical package properties require a
superseding package (`supersession_relationship=REQUIRES_SUPERSEDING_PACKAGE`
or `FULL_SUPERSESSION`); a sidecar entry alone is insufficient.

See templates under `witness-package/templates/` for entry grammar.
