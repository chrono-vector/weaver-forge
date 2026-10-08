"""Persistent INR event/challenge ledger (JSONL, sha256 hash chain, head record).

Each line is one entry; ``entry_sha256`` is plain SHA-256 over the canonical JSON
of the entry without that field, and ``prev_entry_sha256`` chains to the previous
line ("0" * 64 for the first). Entries are only ever appended. A broken chain,
an unknown entry kind or a malformed line makes the ledger unusable (fail closed).

r3 head record (cheap fail-closed improvement, no redesign): after every append the
ledger writes ``<ledger>.head`` = {"seq", "entry_sha256"} of the newest entry. On
every read the recorded head entry must still be present at its sequence number, so
truncating/replacing the ledger below the head, or deleting the ledger while the
head remains, fails closed; a non-empty ledger without a head record (including an
r2 ledger) is refused.

LIMITATION (documented, not hidden): integrity assumes protected persistent
history. A writer that deletes or rewrites BOTH the ledger and its head record (or
the whole ledger directory) produces a state indistinguishable from a fresh ledger.
Truncation/deletion is therefore outside the local freshness guarantee unless the
ledger location is independently protected. This is a local replay guard; it is NOT
strong append-only tamper evidence (no external anchoring, no signatures).

The default location is outside any repository worktree so capture runs do not
dirty the tree. Tests and callers may pass an explicit path.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time

GENESIS = "0" * 64
KINDS = ("RESERVED", "COMPLETED", "REJECTED")
_KEYS = frozenset({"seq", "prev_entry_sha256", "kind", "event_id", "challenge",
                   "recorded_at_ns", "detail", "entry_sha256"})
_PACKAGE_WORKTREE = Path(__file__).resolve().parents[2]


class LedgerError(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _entry_digest(entry):
    return hashlib.sha256(_canonical({k: v for k, v in entry.items() if k != "entry_sha256"})).hexdigest()


def default_path():
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        return base / "Weaver" / "inr_001" / "inr_event_ledger_v0.jsonl"
    base = Path(os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
    return base / "weaver" / "inr_001" / "inr_event_ledger_v0.jsonl"


def resolve_path(path=None):
    resolved = Path(default_path() if path is None else path).resolve()
    if resolved == _PACKAGE_WORKTREE or _PACKAGE_WORKTREE in resolved.parents:
        raise LedgerError("INR ledger must live outside the repository worktree")
    return resolved


def head_path(path):
    return Path(str(path) + ".head")


def _read_head(path):
    head = head_path(path)
    if not head.exists():
        return None
    try:
        value = json.loads(head.read_bytes().decode("utf-8"))
    except (UnicodeError, ValueError):
        raise LedgerError("malformed ledger head record") from None
    if (type(value) is not dict or set(value) != {"seq", "entry_sha256"}
            or type(value["seq"]) is not int or value["seq"] < 1
            or type(value["entry_sha256"]) is not str):
        raise LedgerError("malformed ledger head record")
    return value


def read_entries(path):
    path = Path(path)
    head = _read_head(path)
    if not path.exists():
        if head is not None:
            raise LedgerError("ledger deleted while its head record remains")
        return []
    entries, previous = [], GENESIS
    for number, line in enumerate(path.read_bytes().split(b"\n"), 1):
        if not line:
            continue
        try:
            entry = json.loads(line.decode("utf-8"))
        except (UnicodeError, ValueError):
            raise LedgerError(f"malformed ledger line {number}") from None
        if (type(entry) is not dict or set(entry) != _KEYS or entry["kind"] not in KINDS
                or entry["seq"] != len(entries) + 1 or entry["prev_entry_sha256"] != previous
                or entry["entry_sha256"] != _entry_digest(entry)):
            raise LedgerError(f"ledger hash chain broken at line {number}")
        entries.append(entry)
        previous = entry["entry_sha256"]
    if entries and head is None:
        raise LedgerError("ledger head record missing (truncation/replacement cannot be excluded)")
    if head is not None and (len(entries) < head["seq"]
                             or entries[head["seq"] - 1]["entry_sha256"] != head["entry_sha256"]):
        raise LedgerError("ledger truncated or replaced below its recorded head")
    return entries


class _Lock:
    def __init__(self, path):
        self.lock = Path(str(path) + ".lock")
        self.fd = None

    def __enter__(self):
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + 10
        while True:
            try:
                self.fd = os.open(self.lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise LedgerError("INR ledger is locked; refusing to proceed") from None
                time.sleep(0.05)

    def __exit__(self, *exc):
        os.close(self.fd)
        os.unlink(self.lock)
        return False


def _append(path, entries, kind, event_id, challenge, detail):
    entry = {"seq": len(entries) + 1,
             "prev_entry_sha256": entries[-1]["entry_sha256"] if entries else GENESIS,
             "kind": kind, "event_id": event_id, "challenge": challenge,
             "recorded_at_ns": time.time_ns(), "detail": detail}
    entry["entry_sha256"] = _entry_digest(entry)
    with open(path, "ab") as handle:
        handle.write(_canonical(entry) + b"\n")
        handle.flush()
        os.fsync(handle.fileno())
    head, temporary = head_path(path), Path(str(path) + ".head.tmp")
    with open(temporary, "wb") as handle:
        handle.write(_canonical({"seq": entry["seq"], "entry_sha256": entry["entry_sha256"]}))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, head)
    return entry


def reserve(path, event_id, challenge):
    """Reserve an event ID and challenge before any target execution."""
    with _Lock(path):
        entries = read_entries(path)
        for entry in entries:
            if entry["kind"] != "RESERVED":
                continue
            if entry["event_id"] == event_id:
                _append(path, entries, "REJECTED", event_id, challenge,
                        {"reason": "event ID replay"})
                raise LedgerError("event ID already used in the INR ledger")
            if entry["challenge"] == challenge:
                _append(path, entries, "REJECTED", event_id, challenge,
                        {"reason": "challenge replay"})
                raise LedgerError("challenge already used in the INR ledger")
        return _append(path, entries, "RESERVED", event_id, challenge, {})


def complete(path, event_id, challenge, detail):
    """Record the final outcome of a reserved event (PASS or not)."""
    with _Lock(path):
        entries = read_entries(path)
        reserved = [e for e in entries if e["kind"] == "RESERVED" and e["event_id"] == event_id]
        done = [e for e in entries if e["kind"] == "COMPLETED" and e["event_id"] == event_id]
        if len(reserved) != 1 or reserved[0]["challenge"] != challenge or done:
            raise LedgerError("completion without a single open reservation")
        return _append(path, entries, "COMPLETED", event_id, challenge, detail)


def lookup(path, event_id):
    entries = read_entries(path)
    pick = lambda kind: [e for e in entries if e["kind"] == kind and e["event_id"] == event_id]
    reserved, completed = pick("RESERVED"), pick("COMPLETED")
    if len(reserved) > 1 or len(completed) > 1:
        raise LedgerError("duplicate ledger records for event")
    return (reserved[0] if reserved else None), (completed[0] if completed else None)
