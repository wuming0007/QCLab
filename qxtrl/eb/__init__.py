"""EB (L3 / Execution Backend).

Implements the contract in QXtrl_L3_EB_ExecutionBackend_设计.md.
MVP focus: VirtualExecutionBackend that accepts/validates CompiledBundle from L2/CPIR
and produces BackendRunResult using the existing virtual runner (L7).

The verify_compiled_bundle tool (provided by L2) is the recommended entry point
for bundle validation, usable uniformly by L3, L4, L5.
"""

from .models import (
    BackendSubmitRequest,
    BackendCapability,
    BackendDiagnostic,
    BackendEvent,
    BackendRunResult,
    ExecutionBackend,
)
from .virtual import VirtualExecutionBackend
from qxtrl.cpir import verify_compiled_bundle  # re-export for convenience

__all__ = [
    "BackendSubmitRequest",
    "BackendCapability",
    "BackendDiagnostic",
    "BackendEvent",
    "BackendRunResult",
    "ExecutionBackend",
    "VirtualExecutionBackend",
    "verify_compiled_bundle",
]
