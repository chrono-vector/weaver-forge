"""INR-001 v0 re-check of disk-loaded records: INFORMATIONAL_RECHECK only.

Fresh PASS-capable results exist only as the report printed by a trusted
supervisor process (``supervisor_inr_v0``) about children it launched itself in the
same execution. Anything loaded from disk or supplied by a caller (event exports,
reports, ledger entries) is historical data: this module checks its schema, ledger
consistency and stream digests and returns FAIL / BLOCKED / UNCONFIRMED. It can
never return PASS and never turns a recorded PASS into fresh evidence. It has no
API that accepts evidence objects and no live verification path.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
import sys

from docs.inr_001 import ledger
from docs.inr_001.schema_check import check
from docs.inr_001.supervisor_inr_v0 import NONCLAIMS, canonical, digest

ROOT = Path(__file__).resolve().parent
RECHECK_SCHEMA_VERSION = "inr.verifier.recheck.v0.r3"


def load_schema():
    return json.loads((ROOT / "schema/inr_event_v0.schema.json").read_bytes())


def recheck_export(export, *, ledger_path=None):
    """Informational re-check of a disk export. Never PASS, never fresh evidence."""
    fail, blocked = [], []
    unconfirmed = ["recheck: disk/caller-provided records are informational and never fresh PASS evidence"]
    problems = check(export, load_schema())
    if problems:
        fail.extend("schema: " + p for p in problems)
    else:
        try:
            reserved, completed = ledger.lookup(ledger.resolve_path(ledger_path), export["inr_event_id"])
        except (ledger.LedgerError, OSError) as exc:
            reserved, completed = None, None
            fail.append("ledger: " + str(exc))
        if (reserved is None or completed is None
                or reserved["challenge"] != export["challenge"]
                or completed["challenge"] != export["challenge"]
                or reserved["entry_sha256"] != export["ledger_reservation_entry_sha256"]
                or completed["detail"].get("export_sha256") != digest(canonical(export))):
            fail.append("ledger: export not recorded in the ledger or altered after capture")
        else:
            recorded = completed["detail"].get("derived_result")
            if recorded == "BLOCKED":
                blocked.append("ledger: recorded live result was BLOCKED")
            elif recorded == "FAIL":
                fail.append("ledger: recorded live result was FAIL")
            elif recorded == "PASS":
                unconfirmed.append("ledger: a recorded PASS is history, not fresh evidence")
        for record in export["capture_records"]:
            for stream in ("stdout", "stderr"):
                try:
                    raw = base64.b64decode(record[stream + "_base64"], validate=True)
                except ValueError:
                    fail.append("recheck: invalid stream encoding")
                    continue
                if digest(raw) != record[stream + "_sha256"]:
                    fail.append("recheck: stream changed after capture")
    derived = "BLOCKED" if blocked else "FAIL" if fail else "UNCONFIRMED"
    return {"schema_version": RECHECK_SCHEMA_VERSION, "result_kind": "INFORMATIONAL_RECHECK",
            "derived_result": derived, "pass_allowed": False, "fresh_pass_capable": False,
            "blocked": blocked, "fail": fail, "unconfirmed": unconfirmed, "nonclaims": list(NONCLAIMS)}


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    ledger_path = None
    if len(args) == 3 and args[1] == "--ledger":
        ledger_path = args[2]
    elif len(args) != 1:
        print("usage: python -m docs.inr_001.validate_inr_v0 EXPORT.json [--ledger PATH]", file=sys.stderr)
        return 2
    try:
        export = json.loads(Path(args[0]).read_bytes())
        result = recheck_export(export, ledger_path=ledger_path)
    except (OSError, UnicodeError, ValueError) as exc:
        result = {"schema_version": RECHECK_SCHEMA_VERSION, "result_kind": "INFORMATIONAL_RECHECK",
                  "derived_result": "FAIL", "pass_allowed": False, "fresh_pass_capable": False,
                  "blocked": [], "fail": [str(exc)], "unconfirmed": [], "nonclaims": list(NONCLAIMS)}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
