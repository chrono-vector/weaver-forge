# PSM-001 Verification

This record captures local implementation validation only. It is not Human
Final, independent reproduction, evidence promotion, authority, or production
authorization.

## Focused results

- Representative PSM-v0 record validation: `VALID`
- Focused PSM tests: `28/28 PASS`
- Required PSM mutations: `13/13 KILLED`

Commands:

```powershell
python docs/portfolio_state/validate_psm_v0.py docs/portfolio_state/portfolio_state_v0.example.json --repository .
python -m unittest docs.portfolio_state.test_validate_psm_v0 docs.portfolio_state.test_mutations
```

The focused cases were executed unchanged in bounded named groups because the
host terminates a single Windows process at approximately 60 seconds. All 28
focused cases and all 13 mutation cases ran in successful groups; no case was
skipped or altered.

The focused suite covers closed top-level and nested fields, deterministic
serialization, duplicate JSON key rejection, Git-object source resolution,
accepted Human Final linkage and code-owned claim-to-source interpretation pins
for Earned entries, canonical bound descriptions, missing source rejection,
Earned/NotYetEarned contradiction detection, debt-reference integrity,
FAIL/remediation/PASS preservation, UNKNOWN separation from PASS, replayability
separation from independent reproduction, and rejection of authority, Human
Final, production permission, promotion, and ceiling-override metadata.

Required mutations M1 through M9 remain detected: unsupported promotion from
NotYetEarned, blocking-debt deletion, limitation-to-authority conversion,
counterexample-history erasure, UNKNOWN-to-PASS conversion, Human Final
inference, production-permission inference, independent-reproduction inference,
and unresolved-source substitution. Remediation mutations M10 through M13 are
also killed: unrelated accepted-source substitution for a stronger claim,
NotYetEarned/debt removal followed by unsupported Earned injection, complete
required-counterexample deletion, and PASS-only history collapse.

## Material remediation closure

- Unrelated accepted source text cannot support another claim: `PASS`
- ECP closure/verification cannot support production authorization: `PASS`
- Removing NotYetEarned or ValidationDebt creates no evidence: `PASS`
- A required counterexample record cannot be deleted: `PASS`
- Required negative-evidence and remediation links cannot be deleted: `PASS`
- `FAIL` / `REMEDIATION` / `PASS` cannot collapse to final PASS: `PASS`

## Existing Weaver regression

- `python scripts/validate_receipts.py`: `PASS` (15/15 listed receipts)
- `python -m unittest tools.ecp.test_checkpoint tools.ecp.test_mutations`:
  `32/32 PASS`
- `python -m unittest tools.wacp.test_wacp`: `35/35 PASS`

The WACP cases were executed unchanged in bounded groups of at most four because
the host terminates a single Windows process at approximately 60 seconds. All
35 named cases ran exactly once across the successful groups; no case was
skipped or altered.

## Self-review boundaries

- New authority: `NO`
- Evidence promotion path: `NO`
- Human Final inference: `NO`
- Production permission inference: `NO`
- SEIC semantic change: `NO`
- WACP semantic change: `NO`
- ECP semantic change: `NO`
- New digest domain: `NO`
- Transition Certificate: `NO`
- Scope beyond metadata/schema/lint validation: `NO`

## Evidence ceiling and limitations

Evidence is limited to local PSM-v0 implementation, synthetic validation,
source-link resolution against locally available Git objects, and local
regression results at the pinned repository state. Source-record authority and
protection remain outside PSM. PSM does not discover omitted debt, assumptions,
counterexamples, or sources, and a `VALID` result does not establish portfolio
truth, correctness, safety, completeness, or authorization.
