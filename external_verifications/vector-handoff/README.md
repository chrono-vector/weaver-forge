# VECTOR Package Ingress v0

This directory is a Weaver Forge **read-only ingress boundary** for Owner-authorized VECTOR handoff packages.

It is **not** Independent Witness, Evidence admission, Truth verification, Replay authorization, Weaver execution, Stage 6, C-014, RC9, or a continuation of WF-FC-04.

```text
VECTOR Ingress ≠ Independent Witness
VECTOR Ingress ≠ Evidence admission
VECTOR Ingress ≠ Truth verification
VECTOR Ingress ≠ Replay authorization
VECTOR Ingress ≠ Stage 6
INGRESS_READY ≠ Evidence Admitted
INGRESS_READY ≠ Truth Verified
INGRESS_READY ≠ Replay Authorized
INGRESS_READY ≠ Weaver Execution Authorized
INGRESS_READY ≠ Stage 6 Authorized
INGRESS_READY ≠ Independent Witness PASS
```

v0 public input is a ZIP path only. The evaluator returns a data object (optional stdout). It does not write into the package, this repository, VECTOR, Chronicle, or witness-submissions.

See `vector-ingress-v0/` for the implementation.
