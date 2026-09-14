from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from . import AdapterResult, ExecutionAdapter, VectorResult


class HashClaimAdapter(ExecutionAdapter):
    """
    Generic adapter for claims of the form:
      file X has SHA-256 Y, and optional transformation Z is reproducible.

    Fresh third-party targets can be ordinary files/dirs with a declared digest.
    """

    name = "hash_claim"

    def execute(self, pinned_root: Path, claim: dict[str, Any], evidence_raw: Path) -> AdapterResult:
        params = claim.get("adapter_params") or {}
        logs: list[str] = []
        vectors: list[VectorResult] = []

        primary_name = params.get("primary_file")
        expected = (params.get("expected_sha256") or "").lower()
        mode = params.get("mode", "verify_digest")  # verify_digest | force_fail | incomplete

        files = sorted(p for p in pinned_root.rglob("*") if p.is_file())
        if not files:
            return AdapterResult(
                claim_result="BLOCKED",
                vectors=[
                    VectorResult(
                        id="EXEC_TARGET_PRESENT",
                        result="FAIL",
                        detail={"error": "NO_PINNED_FILES"},
                    )
                ],
                logs=["no pinned files"],
            )

        primary = None
        if primary_name:
            candidates = [p for p in files if p.name == primary_name or p.as_posix().endswith(primary_name)]
            primary = candidates[0] if candidates else None
        else:
            primary = files[0]

        if primary is None:
            vectors.append(
                VectorResult(
                    id="EXEC_TARGET_PRESENT",
                    result="FAIL",
                    detail={"error": "PRIMARY_FILE_MISSING", "primary_file": primary_name},
                )
            )
            return AdapterResult(claim_result="FAIL", vectors=vectors, logs=logs)

        actual = hashlib.sha256(primary.read_bytes()).hexdigest()
        logs.append(f"primary={primary} sha256={actual}")

        # Positive digest check
        if mode == "incomplete":
            # Deliberately omit required evidence vector / leave incomplete
            vectors.append(
                VectorResult(
                    id="POSITIVE_DIGEST_MATCH",
                    result="PASS",
                    detail={"note": "incomplete mode skips required controls"},
                )
            )
            (evidence_raw / "partial_only.json").write_text(
                json.dumps({"incomplete": True}), encoding="utf-8"
            )
            return AdapterResult(
                claim_result="INCONCLUSIVE",
                vectors=vectors,
                artifacts={"incomplete": True},
                logs=logs + ["incomplete evidence condition"],
            )

        digest_ok = bool(expected) and actual == expected.lower()
        if mode == "force_fail":
            digest_ok = False
        vectors.append(
            VectorResult(
                id="POSITIVE_DIGEST_MATCH",
                result="PASS" if digest_ok else "FAIL",
                detail={
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                    "primary_file": str(primary),
                },
            )
        )

        # Negative: wrong expected digest must not match
        wrong = ("0" * 63) + "1"
        wrong_ok = actual != wrong
        vectors.append(
            VectorResult(
                id="NC1_WRONG_DIGEST_REJECTED",
                result="PASS" if wrong_ok else "FAIL",
                detail={"wrong_digest": wrong, "equals_actual": actual == wrong},
            )
        )

        # Tamper: flip one byte of a working copy and ensure digest changes
        original = primary.read_bytes()
        if not original:
            tampered = b"\x00"
        else:
            b = bytearray(original)
            b[0] ^= 0x01
            tampered = bytes(b)
        tampered_digest = hashlib.sha256(tampered).hexdigest()
        tamper_path = evidence_raw / "tampered_primary.bin"
        tamper_path.write_bytes(tampered)
        tamper_ok = tampered_digest != actual
        vectors.append(
            VectorResult(
                id="T1_TAMPER_CHANGES_DIGEST",
                result="PASS" if tamper_ok else "FAIL",
                detail={
                    "original_sha256": actual,
                    "tampered_sha256": tampered_digest,
                    "tampered_path": str(tamper_path),
                },
            )
        )

        # Reproduction: re-hash same bytes
        again = hashlib.sha256(primary.read_bytes()).hexdigest()
        repro_ok = again == actual
        vectors.append(
            VectorResult(
                id="R1_REHASH_REPRODUCTION",
                result="PASS" if repro_ok else "FAIL",
                detail={"first": actual, "second": again},
            )
        )

        required = [
            "POSITIVE_DIGEST_MATCH",
            "NC1_WRONG_DIGEST_REJECTED",
            "T1_TAMPER_CHANGES_DIGEST",
            "R1_REHASH_REPRODUCTION",
        ]
        by_id = {v.id: v for v in vectors}
        claim_pass = all(by_id[i].result == "PASS" for i in required)

        artifacts = {
            "primary_file": str(primary),
            "actual_sha256": actual,
            "inventory": [
                {
                    "path": str(p.relative_to(pinned_root)).replace("\\", "/"),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                }
                for p in files
            ],
        }
        (evidence_raw / "adapter_result.json").write_text(
            json.dumps(
                {
                    "claim_result": "PASS" if claim_pass else "FAIL",
                    "vectors": [v.__dict__ for v in vectors],
                    "artifacts": artifacts,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        return AdapterResult(
            claim_result="PASS" if claim_pass else "FAIL",
            vectors=vectors,
            artifacts=artifacts,
            logs=logs,
        )


def get_adapter(name: str) -> ExecutionAdapter:
    if name == "hash_claim":
        return HashClaimAdapter()
    raise ValueError(f"unknown adapter: {name}")
