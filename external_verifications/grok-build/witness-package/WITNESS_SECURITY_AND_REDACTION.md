# Security and redaction — Witness package

## Do not publish

- API keys, tokens, cookies
- SSH private keys, Git credentials
- Unnecessary full home-directory paths
- Private email addresses (unless you intentionally make them public)
- Sensitive hostnames or cloud account IDs
- Unrelated environment dumps

## Do before submission

Review all logs. Redact secrets, marking redactions:

```text
[REDACTED: Git credential]
[REDACTED: path under home directory]
```

## Must remain visible after redaction

- Source commit
- Image digest
- Build command
- Exit code
- Artifact SHA-256 and size
- Enough environment detail to judge independence (OS, Docker version, arch)

## Product / auth

Do not introduce product authentication materials. This Witness scope has **no** product login.
