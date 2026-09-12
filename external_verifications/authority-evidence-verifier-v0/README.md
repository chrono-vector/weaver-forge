# Weaver Authority Evidence Verifier v0

Validates and normalizes existing authority evidence packs (CARO overlays).
Does **not** perform RPC reads, execute privileged actions, or mutate CAW.

Design: `WAEID-20260912-132447-D4AAEF36` (architecture D).

Independent axes (no single AUTHORITY_COMPLETE):

- `AUTHORITY_MECHANISM_STATUS`
- `AUTHORITY_STATE_READ_STATUS`
- `AUTHORITY_HOLDER_ADDRESS_STATUS`
- `AUTHORITY_HOLDER_IDENTITY_STATUS`
- `AUTHORITY_SCOPE_STATUS`
- `AUTHORITY_MUTABILITY_STATUS`
- `PRIVILEGED_EXECUTION_STATUS`
- `LIVE_AUTHORITY_ACTION_STATUS`

Hard separations:

- architecture mapped ≠ privileged execution ≠ live authority action
- holder address ≠ holder identity
- user-asset authorization ≠ protocol admin
- permissionless function ≠ system permissionless

```bash
python authority_evidence_verifier_v0.py --emit-caro-pack > fixtures/caro_authority_evidence_pack.json
python authority_evidence_verifier_v0.py --verify-caro
python -m unittest tests/test_authority_evidence_verifier_v0.py
```

Optional consumers:

- `attach_authority_link_to_runtime_verifier_result_v0` (link-only; no runtime promotion)
- `attach_authority_evidence_to_synthesizer_paths_v0` (does not alter STATIC COMPLETE/PARTIAL)
