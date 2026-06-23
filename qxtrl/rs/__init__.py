"""RS (L4 / Runtime & Scheduler).

Implements the contract in QXtrl_L4_RS_RuntimeScheduler_设计.md.
MVP: single-process synchronous run_once() for Rabi virtual, orchestrating L2/L3/L6/L5.
"""

from .models import (
    RunRequest,
    RunReceipt,
    RunState,
    RunEvent,
    RuntimeDiagnostic,
    StageTiming,
    ResourceLease,
    RetryPolicy,
    RuntimeRunResult,
)
from .service import RuntimeService

__all__ = [
    "RunRequest",
    "RunReceipt",
    "RunState",
    "RunEvent",
    "RuntimeDiagnostic",
    "StageTiming",
    "ResourceLease",
    "RetryPolicy",
    "RuntimeRunResult",
    "RuntimeService",
]
