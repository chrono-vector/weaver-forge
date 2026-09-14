# hash_claim example

Sanitized portable example for Weaver Forge. Synthetic data only. Relative paths only.

## Target

`target/payload.txt` — fixed UTF-8 content (LF line endings).

Pinned SHA-256:

```
bb79743593377b90ff841e7786c3b2b63068e967d8b6baa00138f82a934cc295
```

## Reproduce (from repository root)

Write all run output to a disposable directory **outside this repository** (do not use `examples/hash_claim/runs/`).

```bash
# POSIX example — any directory outside the source tree
OUT="${TMPDIR:-/tmp}/weaver-forge-hash-claim-runs"
mkdir -p "$OUT"

python -m audit_lifecycle.cli run \
  --request examples/hash_claim/request.json \
  --out "$OUT"
```

```powershell
# Windows PowerShell example
$OUT = Join-Path $env:TEMP "weaver-forge-hash-claim-runs"
New-Item -ItemType Directory -Force -Path $OUT | Out-Null

python -m audit_lifecycle.cli run `
  --request examples/hash_claim/request.json `
  --out $OUT
```

A successful run with this request auto-freezes (human review disabled for the minimal demo).

```bash
# replace <audit_id> with the directory printed under $OUT/
python -m audit_lifecycle.cli verify --run "$OUT/<audit_id>"
```

Expect: decision PASS, freeze present, `verify_ok=true`.

Second freeze must fail closed:

```bash
python -m audit_lifecycle.cli freeze --run "$OUT/<audit_id>"
```

Expect: `FREEZE_ALREADY_EXISTS`.

## Notes

- Keep generated run trees outside the source tree; do not create `examples/hash_claim/runs/`.
- Do not substitute private evidence paths into this example.
