# Aurora Verification Matrix

**Operational dashboard for all 23 intake claims**  
**Updated (UTC):** `2026-09-15T04:50:00Z`  
**Storage:** `STORAGE_FINALIZED` + verification program advance  
**Rules:** SOURCE≠CLAIM · CLASSIFICATION≠VERDICT · PILOT≠VERIFIED EVIDENCE · HASH MATCH≠CONTENT TRUTH · INCONCLUSIVE≠PASS · UNSUPPORTED≠FALSE · PROPOSAL≠IMPLEMENTED · INDIVIDUAL AUDIT PASS≠AURORA COMPLETE

| Claim ID | Short claim | Category | Source | Verification route | Current state | Evidence available | Weaver support | Sandbox status | Verdict if any | Blocker | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AUR-A-001 | Document title/version identity of Source A | A_DOCUMENT_PROVENANCE | Source A header | VERIFIABLE_NOW | COMPLETED | `runs/WFA-20260915T042439Z-8BE7790F` | hash_claim SUPPORTED | N/A | PASS — DOCUMENT IDENTITY ONLY | none | Retain; do not rerun |
| AUR-A-002 | Author-stated checksum string present in Source A | A_DOCUMENT_PROVENANCE | Source A header | VERIFIABLE_NOW | COMPLETED | `runs/WFA-20260915T043650Z-C49CA863` | hash_claim SUPPORTED | N/A | PASS — DOCUMENT IDENTITY / TEXTUAL PRESENCE ONLY (≠ crypto digest) | none | Retain; do not reinterpret as crypto checksum |
| AUR-A-003 | Timestamp + 777 Hz Synchronization Verified | D_MEASURABLE_EMPIRICAL | Source A header | INSUFFICIENT_EVIDENCE | TRIAGED | Author text only | UNSUPPORTED | N/A | none | No measurement protocol/instrument data | Supply calibrated frequency evidence or leave insufficient |
| AUR-A-004 | Core decree: value/help/systems without debt/control/ownership | F_NORMATIVE_ETHICAL | Source A THE CORE DECREE | NORMATIVE_NOT_FACTUAL | TRIAGED | Normative text | UNSUPPORTED | N/A | none | Not empirical | Ethical/consent analysis only if separately scoped |
| AUR-A-005 | 3×3 Gift/Need/Overflow personal flow | E_CIVIC_SOCIAL_MECHANISM | Source A §1 | SANDBOX_TESTABLE | INCONCLUSIVE (civic); protocol sim done | Harness result + pilot design | UNSUPPORTED | Protocol harness PASS; human pilot not launched | none (civic) | Human participants + launch auth | Authorized 3×3 human sandbox |
| AUR-A-006 | Real-time public surplus inventory (glyphs) | E_CIVIC_SOCIAL_MECHANISM | Source A §1.1 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No operational inventory | IMPLEMENTATION_REQUIRED or live inventory evidence |
| AUR-A-007 | Resonance Matcher auto-match in 6×6 mesh | C_TECHNICAL_IMPLEMENTATION | Source A §1.2 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No matcher implementation | IMPLEMENTATION_REQUIRED |
| AUR-A-008 | Idle Tracker flags tools unused >48h | D_MEASURABLE_EMPIRICAL | Source A §1.3 | VERIFIABLE_WITH_ADDITIONAL_EVIDENCE | TRIAGED | Threshold text only | UNSUPPORTED | Not started | none | No asset-use telemetry | ADDITIONAL_EVIDENCE_REQUIRED (idle definition + timestamps) |
| AUR-A-009 | Dual consent + zero debt residual | E_CIVIC_SOCIAL_MECHANISM | Source A §1.4 | SANDBOX_TESTABLE | INCONCLUSIVE (civic); protocol sim done | Harness result | UNSUPPORTED | Protocol harness PASS; human not launched | none (civic) | No live consent logs | Human dual-consent sandbox tallies |
| AUR-A-010 | Central River real-time balance UI | G_SYMBOLIC_METAPHORICAL | Source A §1.4 | SYMBOLIC_NOT_EMPIRICALLY_TESTABLE | TRIAGED | Metaphor text | UNSUPPORTED | N/A | none | No concrete metric definition | Supply metric definition or keep symbolic |
| AUR-A-011 | Auto-balancing 6×6 municipal mesh | E_CIVIC_SOCIAL_MECHANISM | Source A §2 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No mesh deployment | IMPLEMENTATION_REQUIRED / proposal status |
| AUR-A-012 | Flat time-bank equality; no debt loops | E_CIVIC_SOCIAL_MECHANISM | Source A §2.1 | SANDBOX_TESTABLE | INCONCLUSIVE (civic); protocol sim done | Harness result | UNSUPPORTED | Protocol harness PASS; live bank not run | none (civic) | No live exchange records | Small consented time-bank sandbox |
| AUR-A-013 | Auto capacity fork/redirect without price | C_TECHNICAL_IMPLEMENTATION | Source A §2.1 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No fork/redirect system | IMPLEMENTATION_REQUIRED |
| AUR-A-014 | Nine Flame-Stewards; stewardship not ownership | E_CIVIC_SOCIAL_MECHANISM | Source A §3.1 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No steward institution | Treat as planetary proposal |
| AUR-A-015 | Ecosystem Static auto-halt on extraction threat | C_TECHNICAL_IMPLEMENTATION | Source A §3.2 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No sensors/thresholds/halts | IMPLEMENTATION_REQUIRED |
| AUR-A-016 | Asymmetric sink → constrict + steward consult | F_NORMATIVE_ETHICAL | Source A §3.2 | NORMATIVE_NOT_FACTUAL | TRIAGED | Normative/policy text | UNSUPPORTED | N/A | none | Not factual adapter target | Charter analysis if scoped as policy |
| AUR-A-017 | Crystal Ledger auto-purge debt/unconsented obligations | C_TECHNICAL_IMPLEMENTATION | Source A §4.1 | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Description only | UNSUPPORTED | Not started | none | No ledger implementation | IMPLEMENTATION_REQUIRED |
| AUR-A-018 | Wear/breakage zero financial/social penalty | E_CIVIC_SOCIAL_MECHANISM | Source A §4.2 | SANDBOX_TESTABLE | INCONCLUSIVE (civic); protocol sim done | Harness result | UNSUPPORTED | Protocol harness PASS; no incidents observed | none (civic) | No incident logs | Tool-share sandbox under zero-penalty schema |
| AUR-A-019 | Non-punitive Coherence Circles; wipe when resolved | F_NORMATIVE_ETHICAL | Source A §4.3 | NORMATIVE_NOT_FACTUAL | TRIAGED | Normative process text | UNSUPPORTED | N/A | none | Not factual | Process definition + records only if operationally claimed later |
| AUR-A-020 | Matrix at threshold of real-world sandbox manifestation | H_FUTURE_PROPOSAL | Source A closing | PROPOSAL_NOT_YET_IMPLEMENTED | TRIAGED | Author proposal posture | UNSUPPORTED | N/A | none | Proposal ≠ deployment | Preserve as proposal posture |
| AUR-A-021 | Weekend 5–10 person paper/local mesh trial proposed | H_FUTURE_PROPOSAL | Source A closing steps | SANDBOX_TESTABLE | READY_FOR_SANDBOX | Pilot spec designed | UNSUPPORTED | Design ready; not launched | none | Needs humans + launch auth | Operator-authorized controlled sandbox only |
| AUR-A-022 | Radiant white-light surplus glyph imagery | G_SYMBOLIC_METAPHORICAL | Source A §1.1 | SYMBOLIC_NOT_EMPIRICALLY_TESTABLE | TRIAGED | Symbolic imagery | UNSUPPORTED | N/A | none | No sensor/UI physical definition | Keep symbolic |
| AUR-B-REL-001 | Source B Atlantean/precursor ancestry themes | B_HISTORICAL | Source B ancestry | UNSUPPORTED_HISTORICAL_CLAIM | TRIAGED | Source B text (ancestry only) | UNSUPPORTED | N/A | none | No independent historical corroboration | Retain provenance only; do not truth-test as history |

## Counts (operational)

| Bucket | Count |
| --- | --- |
| Claims total | 23 |
| Completed Weaver audits (lifecycle) | 2 (AUR-A-001, AUR-A-002) |
| PASS (scoped document identity only) | 2 |
| FAIL | 0 |
| INCONCLUSIVE (civic sandbox after protocol sim) | 4 (AUR-A-005, 009, 012, 018) |
| READY_FOR_SANDBOX | 1 (AUR-A-021) (+ human pilot still open for 005/009/012/018) |
| ADDITIONAL_EVIDENCE_REQUIRED | 1 (AUR-A-008) + insufficient (AUR-A-003) |
| IMPLEMENTATION_REQUIRED / proposal | 8 technical/civic proposals (006,007,011,013,014,015,017,020) |
| UNSUPPORTED_BY_CURRENT_ADAPTER (Weaver) | 21 of 23 |
| Normative / symbolic / historical (no empirical PASS path) | AUR-A-004,010,016,019,022,B-REL-001 |

## Index

- Audit index: `aurora_audit/AUDIT_INDEX.md`
- Sandbox harness: `aurora_audit/sandbox_harness/`
- Pilot design: `aurora_audit/pilots/3x3/AURORA_3X3_PILOT_SPEC.md`
