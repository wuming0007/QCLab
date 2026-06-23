"""CPIR (L2 / Compiler / Pulse IR).

Implements the contract in QXtrl_L2_CPIR_Compiler_PulseIR_设计.md.
Current implementation supports the thin Rabi MVP slice while moving toward
stable Pydantic schemas, structured Sweep, CompiledBundle and hashes.
"""

from .compiler import compile_experiment_spec, compile_to_bundle, verify_compiled_bundle
from .pulse_ir import (
    PulseIR,
    PulseMoment,
    FrameEvent,
    SweepSpec,
    SweepAxis,
    AcquireWindow,
    ResourceUsage,
    CompileDiagnostic,
    CompiledBundle,
)

__all__ = [
    "compile_experiment_spec",
    "compile_to_bundle",
    "verify_compiled_bundle",
    "PulseIR",
    "PulseMoment",
    "FrameEvent",
    "SweepSpec",
    "SweepAxis",
    "AcquireWindow",
    "ResourceUsage",
    "CompileDiagnostic",
    "CompiledBundle",
]
