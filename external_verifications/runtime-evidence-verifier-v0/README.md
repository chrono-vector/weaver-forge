# Weaver Runtime Evidence Verifier v0

Validates and normalizes existing runtime evidence packs.
Does **not** execute forks, call RPC, discover paths, or mutate CAW.

Design: `WREID-20260912-113817-2D2509C8` (architecture D).

**RUN_STAGE vs EVIDENCE_STATUS:** `record.level` (VR0..VR3) is campaign chronology.
Axes (`RUNTIME_*_STATUS`) and `highest_runtime_level` are evidence capability derived
from proven facts. Success at V-R1 may establish `LOCAL_EXECUTION_ALIGNED` without
V-R2/V-R3 records. `LOCAL_EXECUTION_ALIGNED` never implies live tx or persistent commit.

```bash
python runtime_evidence_verifier_v0.py --emit-p0014-pack > fixtures/p0014_runtime_evidence_pack.json
python runtime_evidence_verifier_v0.py --emit-p0030-pack > fixtures/p0030_runtime_evidence_pack.json
python runtime_evidence_verifier_v0.py input.json
python -m unittest tests/test_runtime_evidence_verifier_v0.py
```

Safety flags always false: `runtime_execution_verified`, `execution_authorized`, `live_match_verified`.

`R3_LOCAL_EXECUTION_ALIGNED` is a capability label (local execution aligned); it is not a claim that a V-R3 run occurred, and never implies `LIVE_TRANSACTION_VERIFIED`.

Optional synthesizer consumer: `attach_runtime_evidence_to_synthesizer_paths_v0(synth, verifier)` joins by `PATH_ID` without merging into `STATIC_PATH_STATUS`.
