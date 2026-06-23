"""EL (L1 Experiment Language).

Provides structured, recursive PDCA-based ExperimentSpec / AtomSpec (MVP)
for describing experiment intent in a verifiable, compilable way.

Depends on L0/CC (qxtrl/cc) for contracts (IDs, Quantity, L0SnapshotRef, gates, errors).
Does not generate waveforms or perform I/O.

See docs/planning/QXtrl_L1_Experiment_Language_设计.md for full spec.
"""

from .models import (
    ExperimentSpec,
    AtomSpec,
    PlanSpec,
    DoSpec,
    CheckSpec,
    ActSpec,
    TargetSpec,
    ScanSpec,
    ScanAxisSpec,
    AcquisitionSpec,
    L0ContextRef,
    PDCAPathItem,
    NodeIOContract,
    TypedRef,
    RegistryEntry,
    ParameterProposalTarget,
    create_rabi_experiment_spec,
    create_time_rabi_experiment_spec,
    registry,
)

__all__ = [
    "ExperimentSpec",
    "AtomSpec",
    "PlanSpec",
    "DoSpec",
    "CheckSpec",
    "ActSpec",
    "TargetSpec",
    "ScanSpec",
    "ScanAxisSpec",
    "AcquisitionSpec",
    "L0ContextRef",
    "PDCAPathItem",
    "NodeIOContract",
    "TypedRef",
    "RegistryEntry",
    "ParameterProposalTarget",
    "create_rabi_experiment_spec",
    "create_time_rabi_experiment_spec",
    "registry",
]