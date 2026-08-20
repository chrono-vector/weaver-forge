"""VECTOR Package Ingress v0 evaluator.

Public input: ZIP path only. Returns a result dict. Writes nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    from .package_reader_v0 import read_vector_zip_v0
    from .checks_v0 import run_logical_checks
    from .result_v0 import (
        CHECK_NAMES,
        build_ingress_result_v0,
        validate_vector_ingress_result_v0,
    )
except ImportError:
    from package_reader_v0 import read_vector_zip_v0
    from checks_v0 import run_logical_checks
    from result_v0 import (
        CHECK_NAMES,
        build_ingress_result_v0,
        validate_vector_ingress_result_v0,
    )


def evaluate_vector_package_ingress_v0(zip_path: Path | str) -> dict[str, Any]:
    path = Path(zip_path)
    operational = {"zip_path": str(path)}
    read = read_vector_zip_v0(path)
    if not read["ok"]:
        checks = {name: "not_evaluated" for name in CHECK_NAMES}
        checks["container"] = "failed"
        paired = list(zip(read["reason_codes"], read["messages"]))
        return build_ingress_result_v0(
            source_package_id="",
            package_digest=read.get("zip_sha256") or "",
            manifest_digest="",
            checks=checks,
            reason_codes=read["reason_codes"],
            limitation_codes=[],
            reason_messages=paired,
            operational=operational,
        )

    logical = run_logical_checks(read["files"], path.name)
    return build_ingress_result_v0(
        source_package_id=logical["package_id"],
        package_digest=read["zip_sha256"],
        manifest_digest=logical["manifest_digest"],
        checks=logical["checks"],
        reason_codes=[c for c, _ in logical["reasons"]],
        limitation_codes=[c for c, _ in logical["limitations"]],
        reason_messages=logical["reasons"],
        limitation_messages=logical["limitations"],
        operational=operational,
    )


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        sys.stderr.write("usage: ingress_v0.py <package.zip>\n")
        return 1
    result = evaluate_vector_package_ingress_v0(args[0])
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
    disposition = result.get("final_disposition")
    if disposition == "INGRESS_READY":
        return 0
    if disposition == "INGRESS_REJECT":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
