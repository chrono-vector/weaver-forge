"""Command-line entry point for WACP-v0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import generate_pack


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate one deterministic WACP-v0 pack")
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    result = generate_pack(arguments.repository, arguments.manifest, arguments.output)
    print(json.dumps({
        "status": result.status,
        "pack_id": result.pack_id,
        "output_dir": str(result.output_dir) if result.output_dir else None,
        "errors": list(result.errors),
    }, sort_keys=True))
    return 0 if result.status in {"PACK_READY", "PACK_INCOMPLETE", "PACK_TOO_LARGE"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
