# Weaver Runtime Path Synthesizer v0

Static-only synthesis of previously extracted Weaver evidence into bounded runtime-path graphs. Requires source verifier, runtime surface inventory, mutating callsite analyzer, and queue state transition analyzer outputs bound to the same target commit.

Optional input: `static_evidence_graph` (`weaver-static-evidence-graph-v0`). When absent, legacy behavior is preserved.

Optional input: `path_specific_sot_evidence` (`weaver-path-specific-sot-evidence-v0`) and `path_static_clearance_overlay`. Path-usable / dual-valid SoT may satisfy the address axis for `STATIC_PATH_COMPLETE` without a global canonical family. Authority, runtime execution, runtime signer identity, and independent witness are separate axes and do not veto static completion.

Provenance conflicts attach only under subject-scoped relations (subject/contract/file/callsite/chain/consumer ancestry). Zero-source conflicts are preserved in the graph but do not globally block unrelated paths.

```bash
python runtime_path_synthesizer_v0.py input.json
python -m unittest tests.test_runtime_path_synthesizer_v0
python run_caw_acceptance_v8.py
python run_caw_static_completion_sci.py
```

`runtime_execution_verified` is always `false`.  
`STATIC_PATH_COMPLETE` ≠ runtime / authority / IW verified.
