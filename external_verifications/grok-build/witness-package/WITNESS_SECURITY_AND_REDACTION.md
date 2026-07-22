# Security and redaction — Witness package (1.0.0-rc3)

## Before staging or opening a PR

Review **every** staged file:

```bash
git diff --cached --check
git diff --cached
```

Search for sensitive patterns (manual review — **no guarantee** of completeness):

- `token`, `password`, `authorization`, `cookie`
- `private key`, `credential`, `proxy`
- email addresses, cloud account identifiers, local usernames/paths outside the Witness's own
  disposable work root

Inspect Docker and environment logs for accidental secret emission.

## Redaction is permitted only for nonmaterial private-path content, under all of these conditions

A redaction is allowed **only** when **all** of the following hold simultaneously:

1. **Visible replacement marker.** The removed value is replaced in place with a visible
   `[REDACTED: <reason>]` marker (see [templates/REDACTIONS.md](templates/REDACTIONS.md)). Silent
   deletion of a field or line is never acceptable — the reader must always be able to see that a
   redaction occurred and why.
2. **Every redaction is logged.** Every single redaction, no matter how small, is recorded as its
   own enumerated entry in `REDACTIONS.md` with `_file`, `_field`, `_reason`, and
   `_replacement_marker`. An unlogged redaction (a marker present in evidence with no matching
   `REDACTIONS.md` entry, or vice versa) is itself a defect.
3. **Semantic evidence remains intact.** The redaction must not change what the evidence *means*.
   Redacting a local home-directory username inside an otherwise-unrelated path string is
   acceptable; redacting a value that is itself part of what is being verified is not.
4. **Commands, hashes, identities, exit codes, target separation, and failure evidence all remain
   fully readable.** Specifically, a redaction must never obscure, truncate, or partially mask:
   - Exact build/verification commands.
   - Any commit ID, image digest, or `Cargo.lock` SHA-256.
   - Any artifact SHA-256 or size.
   - Any process exit code.
   - Evidence that the `CARGO_TARGET_DIR` (or any other isolation boundary) was empty/separated as
     required.
   - Any evidence of a failure, deviation, mismatch, or negative outcome, in whole or in part.

If a redaction would need to touch any of the categories in point 4, it is not permitted — record
the value as-is, or, if genuinely sensitive and unavoidable, do not submit that evidence file at
all and record the gap honestly as a `MATERIAL_NONCANONICAL` deviation instead of redacting it.

## No redaction may hide, alter, or soften a material defect

**No redaction may hide, alter, or soften a material defect, deviation, mismatch, failure, or
independence conflict.** This is an absolute rule with no exception: a redaction's only
legitimate purpose is removing personally identifying or environment-specific noise that carries
no evidentiary weight. The moment a proposed redaction would make a run look more compliant,
more successful, more independent, or less deviant than it actually was, it is prohibited —
regardless of how the submitter characterizes their intent.

## Redaction log

Record each redaction in `REDACTIONS.md` (see [templates/REDACTIONS.md](templates/REDACTIONS.md)):

```text
[REDACTED: reason]
```

`redaction_state=NONE` requires zero redactions anywhere in the evidence directory.
`redaction_state=PRESENT` requires every redaction to be enumerated with all four fields, and
`semantic_integrity_declaration=yes` is required unconditionally.

## Never redact (validator-enforced keyword screen)

The structural validator rejects any redaction whose logged field/reason text matches a
prohibited-category keyword. Never redact:

- Mandatory commit IDs and digests (`commit`, `digest`)
- `Cargo.lock` / artifact SHA-256 values (`sha256`, `artifact_sha256`)
- Exact build commands and exit codes (`exit_code`, `exit code`)
- Artifact identity fields (`artifact_size`, size, SHA-256, Build ID)
- Independence statements and AI-assistance disclosure (`independence`)

This validator-enforced list is a floor, not a ceiling — the four-condition test above and the
absolute "no material softening" rule apply even to fields the validator does not keyword-screen.

## Do not publish

- API keys, OAuth tokens, session cookies
- SSH private keys, `.netrc`, git credentials
- Unrelated full environment dumps

## Product / auth

Witness scope includes **no** product login. Do not introduce authentication materials.

## Scanner disclaimer

Pattern search and manual review **do not** guarantee absence of secrets.

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc2 | Prior pre-staging review, redaction log, never-redact, do-not-publish sections |
| 1.0.0-rc3 | Added explicit four-condition test for when nonmaterial private-path redaction is permitted (visible marker; every redaction logged; semantic evidence intact; commands/hashes/identities/exit codes/target separation/failure evidence remain readable); added absolute rule that no redaction may hide, alter, or soften a material defect, deviation, mismatch, failure, or independence conflict; aligned never-redact list with the validator's keyword screen |
