"""TRH (L7 Twin / Replay / HIL) - MVP implementation per design.

Typed VirtualRun + basic Replay inspect.
"""

from .models import (
    TRHDiagnostic,
    TwinModelRef,
    VirtualQPUConfig,
    VirtualRunRequest,
    VirtualRunResult,
    ReplayRequest,
    ReplayPlan,
    ReplayResult,
)
from .virtual import run_rabi_virtual, run_rabi_virtual_typed  # noqa: F401
from .replay import build_replay_plan, replay_manifest  # noqa: F401

__all__ = [
    "TRHDiagnostic",
    "TwinModelRef",
    "VirtualQPUConfig",
    "VirtualRunRequest",
    "VirtualRunResult",
    "run_rabi_virtual",
    "run_rabi_virtual_typed",
    "ReplayRequest",
    "ReplayPlan",
    "ReplayResult",
    "build_replay_plan",
    "replay_manifest",
]
