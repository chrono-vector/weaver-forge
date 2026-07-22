# Public blind audit — recommendations (implemented in C2E-2)

1. Introduce **`WITNESS_PACKAGE_VERSION.md`** with proposed tag `grok-build-witness-v1.0.0-rc1` (human creates tag after review).
2. Add **`run_witness_narrow_build.sh`** and **`container_narrow_build.sh`** (author only; not executed in C2E-2).
3. Pin canonical platform to **Linux x86_64 or WSL2 + Docker Desktop Linux containers**; mark PowerShell-native and macOS as noncanonical.
4. Expand all evidence **templates** with explicit required fields.
5. Add **`validate_witness_evidence.py`** (structure only; synthetic tests).
6. Update classification **precedence** and submission **correction/immutability** policy.
7. Correct public readiness wording to **NOT READY — remediation in progress** while preserving C2E-1 history.
8. Register **C-023** for audit intake only (PASS = recorded, not reproduction).
