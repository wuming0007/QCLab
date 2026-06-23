"""L9 / OI - Operator Interfaces (thin SDK + CLI facade).

MVP: one-button Rabi virtual via L4, plus manifest query.
See QXtrl_L9_OI_OperatorInterfaces_设计.md for scope.
"""

from .models import (
    RunRabiOptions,
    RunSummary,
    OperatorDiagnostic,
    ManifestView,
)
from .sdk import run_rabi_virtual, OperatorSession
from .manifest import show_manifest

__all__ = [
    "RunRabiOptions",
    "RunSummary",
    "OperatorDiagnostic",
    "ManifestView",
    "run_rabi_virtual",
    "OperatorSession",
    "show_manifest",
]