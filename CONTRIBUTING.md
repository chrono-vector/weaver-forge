# Contributing

Thank you for contributing to Weaver Forge.

## Scope

This repository’s product surface is the **audit lifecycle** (`audit_lifecycle/`). Changes should preserve fail-closed evidence behavior.

## Guidelines

- Changes that affect lifecycle semantics **require tests** (extend `audit_lifecycle.tests.test_lifecycle` or add focused tests).
- Evidence and failure paths must remain visible — do not delete FAIL / INCONCLUSIVE / BLOCKED runs to “clean up” outcomes.
- Do not weaken fail-closed boundaries (allowed write root, protected paths, one-shot freeze).
- New claim types require **explicit** adapter + semantic verifier registration; unsupported adapters must fail conservatively.
- Prefer synthetic fixtures and relative paths in examples and tests. Do not commit secrets or private evidence.

## Development checks

```bash
python -m unittest audit_lifecycle.tests.test_lifecycle -v
```

## Pull requests

Describe what the change proves and does not prove. Link failing-before / passing-after commands when behavior changes.
