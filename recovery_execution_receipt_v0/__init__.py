"""Non-authoritative receipts over an externally completed recovery sequence."""

from recovery_execution_receipt_v0.receipt import (
    RecoveryExecutionError,
    build_recovery_execution_receipt,
)

__all__ = ["RecoveryExecutionError", "build_recovery_execution_receipt"]
