# Security and redaction — Witness package (1.0.0-rc2)

## Before staging or opening a PR

Review **every** staged file:

```bash
git diff --cached --check
git diff --cached
```

Search for sensitive patterns (manual review — **no guarantee** of completeness):

- `token`, `password`, `authorization`, `cookie`
- `private key`, `credential`, `proxy`
- email addresses, cloud account identifiers

Inspect Docker and environment logs for accidental secret emission.

## Redaction log

Record each redaction in `REDACTIONS.md` (see [templates/REDACTIONS.md](templates/REDACTIONS.md)):

```text
[REDACTED: reason]
```

## Never redact

- Mandatory commit IDs and digests
- Exact build commands and exit codes
- Artifact identity fields (size, SHA-256, Build ID)
- Independence statements and AI-assistance disclosure

## Do not publish

- API keys, OAuth tokens, session cookies
- SSH private keys, `.netrc`, git credentials
- Unrelated full environment dumps

## Product / auth

Witness scope includes **no** product login. Do not introduce authentication materials.

## Scanner disclaimer

Pattern search and manual review **do not** guarantee absence of secrets.
