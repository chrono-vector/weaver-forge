from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class VectorResult:
    id: str
    result: str  # PASS | FAIL
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdapterResult:
    claim_result: str  # PASS | FAIL | INCONCLUSIVE | BLOCKED
    vectors: list[VectorResult]
    artifacts: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)


class ExecutionAdapter(ABC):
    name: str = "base"

    @abstractmethod
    def execute(self, pinned_root: Path, claim: dict[str, Any], evidence_raw: Path) -> AdapterResult:
        raise NotImplementedError
