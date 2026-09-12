# Independent Witness Verifier v0

Additive IW evidence adjudication for Weaver (Architecture **D**, design `WIWPD-20260912-143017-D82A0D4E`).

## Responsibilities

- Validate IW pack schema and required members
- Validate frozen boundary (CAW commit, Weaver pin, schemas, paths, targets, chain IDs, fixtures, digests)
- Validate required reproduction classes for BOUNDED_D scope
- Validate independence axes with explicit evidence
- Preserve failure and retry history
- Distinguish **MATCHED** from **ACCEPTED**
- Apply nonclaim gates and scope-limited acceptance

## Does NOT

- Run network / RPC
- Execute runtime calls
- Generate witness evidence
- Infer independence from witness name or designation
- Mark real CAW Independent Witness as satisfied from maintainer dry-run

## Status model

`IW_NOT_STARTED` → `IW_IN_PROGRESS` → `IW_REPRODUCTION_PARTIAL` / `IW_REPRODUCTION_MATCHED` → `IW_ACCEPTED` / `IW_REJECTED`

**MATCHED ≠ ACCEPTED.** Designated witness alone ≠ IW satisfied.

## Module layout

- `independent_witness_verifier_v0.py` — verifier
- `schemas/` — IW pack + member schemas
- `tests/` — acceptance + negative tests
- `iw-pack-v1/` — frozen bounded package for future external witness

## Usage

```bash
python independent_witness_verifier_v0.py path/to/iw_pack.json [expected_boundary.json]
python -m unittest discover -s tests -v
```
