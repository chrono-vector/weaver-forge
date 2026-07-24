#!/usr/bin/env python3
"""Materialize Phase 4-S3 rc5 fixture families under tests/fixtures/.

Does not rewrite historical rc4/S1 fixture trees. Uses fixtures_lib rc5 builders
derived from the active S2 schema shapes. Standard library only; no network.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import fixtures_lib

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def main() -> None:
    for scenario in fixtures_lib.RC5_SCENARIOS:
        dest = FIXTURES / scenario
        if dest.exists():
            shutil.rmtree(dest)
        fixtures_lib.build_and_write_rc5(dest, scenario)
        print(f"wrote {dest}")


if __name__ == "__main__":
    main()
