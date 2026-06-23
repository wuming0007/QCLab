"""L1 / EL Experiment Language models (Pydantic).

MVP focus: ExperimentSpec + AtomSpec for Rabi (and similar Atoms later).
Follows the spec in docs/planning/QXtrl_L1_Experiment_Language_设计.md

Key principles (from doc):
- No final waveform ndarray in DoSpec.
- Only Atom touches execution backend.
- Explicit L0 integration (reuse cc validators/gates).
- NodeIOContract for SCP-001.
- PDCA path for audit.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

# Reuse L0/CC contracts (updated package)
from qxtrl.cc import (
    L0SnapshotRef,
    QXtrlValidationError,
    Quantity,
    validate_element_id,
    validate_line_id,
    KNOWN_UNITS,
    ChipModel,
    WiringGraph,
    HardwareInventory,
    SafetyPolicy,
)


# -----------------------------
# Supporting types
# -----------------------------

class L0ContextRef(BaseModel):
    """Explicit reference to required L0 context (snapshots or objects).
    MVP supports str refs or actual loaded L0 model instances for gate checks.
    """
    chip_model_ref: Union[L0SnapshotRef, str, ChipModel]
    wiring_graph_ref: Union[L0SnapshotRef, str, WiringGraph]
    hardware_inventory_ref: Union[L0SnapshotRef, str, HardwareInventory]
    safety_policy_ref: Union[L0SnapshotRef, str, SafetyPolicy]
    calibration_ref: Optional[Union[L0SnapshotRef, str, "Any"]] = None  # type: ignore

    model_config = {"frozen": True}


class PDCAPathItem(BaseModel):
    """Item in the recursive PDCA execution path (for RunManifest)."""
    node_id: str
    node_kind: Literal["atom", "task", "session"]
    pdca_phase: Literal["plan", "do", "check", "act"]
    iteration: Optional[int] = None
    parent_node_id: Optional[str] = None

    model_config = {"frozen": True}


class TypedRef(BaseModel):
    """Generic reference used in NodeIOContract and elsewhere."""
    kind: str  # e.g. "qubit", "line", "l0_snapshot", "parameter", "observation", "proposal"
    ref: str
    optional: bool = False
    unit: Optional[str] = None

    model_config = {"frozen": True}


class TargetSpec(BaseModel):
    """Target element + lines for the experiment (validated against L0)."""
    element_id: str
    drive_line_id: Optional[str] = None
    readout_line_id: Optional[str] = None
    coupler_id: Optional[str] = None
    logical_role: Optional[str] = None

    @field_validator("element_id")
    @classmethod
    def _validate_element(cls, v: str) -> str:
        return validate_element_id(v)

    @field_validator("drive_line_id", "readout_line_id", mode="before")
    @classmethod
    def _validate_lines(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_line_id(v)

    @field_validator("coupler_id", mode="before")
    @classmethod
    def _validate_coupler(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_element_id(v)

    model_config = {"frozen": True}


class ScanAxisSpec(BaseModel):
    axis_id: str
    parameter_ref: str
    unit: str
    values: tuple[float, ...]
    description: Optional[str] = None

    @field_validator("unit")
    @classmethod
    def _validate_unit(cls, v: str) -> str:
        if v not in KNOWN_UNITS:
            raise QXtrlValidationError(f"Unknown unit '{v}'", field="unit", rule="L1-UNIT")
        return v

    @field_validator("parameter_ref")
    @classmethod
    def _validate_parameter_ref(cls, v: str) -> str:
        return _validate_mvp_parameter_ref(v)

    @field_validator("values", mode="before")
    @classmethod
    def _validate_values(cls, v: list) -> tuple[float, ...]:
        if not v:
            raise QXtrlValidationError("scan values cannot be empty", field="values", rule="L1-SCAN")
        cleaned = []
        for val in v:
            if isinstance(val, bool) or (isinstance(val, float) and (val != val or abs(val) == float("inf"))):
                raise QXtrlValidationError("scan values must not contain bool/NaN/Inf", field="values", rule="L1-SCAN")
            # also reject non-numeric after possible input
            if not isinstance(val, (int, float)):
                raise QXtrlValidationError("scan values must be numeric", field="values", rule="L1-SCAN")
            cleaned.append(float(val))
        return tuple(cleaned)

    model_config = {"frozen": True}


class ScanSpec(BaseModel):
    axes: tuple[ScanAxisSpec, ...]
    order: Literal["cartesian", "zipped"] = "cartesian"
    randomization: Literal["none", "shuffled"] = "none"

    model_config = {"frozen": True}


class AcquisitionSpec(BaseModel):
    shots: int
    result_level: Literal["iq", "classified", "counts"] = "iq"
    averaging: Literal["single_shot", "average"] = "average"

    @field_validator("shots")
    @classmethod
    def _validate_shots(cls, v: int) -> int:
        if v <= 0:
            raise QXtrlValidationError("shots must be > 0", field="shots", rule="L1-ACQUISITION")
        return v

    model_config = {"frozen": True}


class PlanSpec(BaseModel):
    objective: str
    target: TargetSpec
    scan: ScanSpec
    acquisition: AcquisitionSpec
    constraints: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}


def _contains_forbidden(obj: Any, forbidden: set[str]) -> bool:
    """Recursively scan dict/list/tuple for any forbidden key at any nesting level."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in forbidden or _contains_forbidden(v, forbidden):
                return True
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _contains_forbidden(item, forbidden):
                return True
    return False


def _validate_mvp_parameter_ref(ref: str) -> str:
    """MVP syntax for parameter_ref (per L1 design).

    - pulse.<role>.<name>  (Rabi MVP restricts role to 'drive' for now)
    - calibration.<element_id>.<logical_channel>.<param>  (element_id validated via L0)
    """
    if not isinstance(ref, str) or not ref:
        raise QXtrlValidationError("parameter_ref must be a non-empty string", field="parameter_ref", rule="L1-PARAM-REF")
    parts = ref.split(".")
    if parts[0] == "pulse":
        if len(parts) < 3:
            raise QXtrlValidationError(
                f"pulse.* parameter_ref must have at least 3 segments (pulse.<role>.<name>): {ref}",
                field="parameter_ref", rule="L1-PARAM-REF"
            )
        # Rabi MVP: only documented drive pulses for now (amplitude/duration/frequency)
        allowed_pulse_roles = {"drive"}
        if parts[1] not in allowed_pulse_roles:
            raise QXtrlValidationError(
                f"pulse role '{parts[1]}' not allowed in Rabi MVP (allowed: {sorted(allowed_pulse_roles)}): {ref}",
                field="parameter_ref", rule="L1-PARAM-REF"
            )
        return ref
    if parts[0] == "calibration":
        if len(parts) < 4:
            raise QXtrlValidationError(
                f"calibration.* parameter_ref must be calibration.<element_id>.<channel>.<param>: {ref}",
                field="parameter_ref", rule="L1-PARAM-REF"
            )
        # Enforce L0 element id rules on the explicit element part
        elem = parts[1]
        validate_element_id(elem)  # will raise QXtrlValidationError with L0 rule if bad
        return ref
    raise QXtrlValidationError(
        f"parameter_ref must start with 'pulse.' or 'calibration.': {ref}",
        field="parameter_ref", rule="L1-PARAM-REF"
    )


class DoSpec(BaseModel):
    atom_ref: str
    pulse_template_ref: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)  # values can be Quantity-like or primitives
    compile_hints: dict[str, Any] = Field(default_factory=dict)

    # Enforce no waveform (MVP + future) — recursive to prevent hiding in nested dicts
    @model_validator(mode="after")
    def _no_waveform(self) -> DoSpec:
        forbidden = {"waveform", "waveforms", "ndarray", "samples", "raw_iq_array", "device_opcode"}
        if _contains_forbidden(self.parameters, forbidden) or _contains_forbidden(self.compile_hints, forbidden):
            raise QXtrlValidationError(
                "DoSpec parameters or compile_hints must not contain waveform/samples/raw device data at any nesting level",
                rule="L1-DO-WAVEFORM",
            )
        return self

    model_config = {"frozen": True}


class CheckSpec(BaseModel):
    analyzer_ref: str
    expected_observation: str
    metrics: tuple[str, ...]
    acceptance: dict[str, Any]

    @model_validator(mode="after")
    def _check_negative_rules(self) -> CheckSpec:
        if not self.analyzer_ref:
            raise QXtrlValidationError("CheckSpec requires analyzer_ref", rule="L1-CHECK")
        if not self.metrics:
            raise QXtrlValidationError("CheckSpec requires non-empty metrics", rule="L1-CHECK")
        if not self.acceptance:
            raise QXtrlValidationError("CheckSpec requires acceptance", rule="L1-CHECK")
        return self

    model_config = {"frozen": True}


class ParameterProposalTarget(BaseModel):
    parameter_ref: str
    source_metric: str

    @field_validator("parameter_ref")
    @classmethod
    def _validate_parameter_ref(cls, v: str) -> str:
        return _validate_mvp_parameter_ref(v)

    model_config = {"frozen": True}


class ActSpec(BaseModel):
    mode: Literal["none", "propose_patch", "request_review"] = "propose_patch"
    proposal_targets: tuple[ParameterProposalTarget, ...] = Field(default_factory=tuple)
    requires_review: bool = False

    @model_validator(mode="after")
    def _act_negative_rules(self) -> ActSpec:
        if self.mode == "propose_patch" and not self.proposal_targets:
            raise QXtrlValidationError(
                "ActSpec.mode='propose_patch' requires proposal_targets",
                rule="L1-ACT",
            )
        return self

    model_config = {"frozen": True}


class NodeIOContract(BaseModel):
    """Node IO contract (SCP-001). Collections are tuples to enforce immutability after construction."""
    consumes: tuple[TypedRef, ...] = Field(default_factory=tuple)
    produces: tuple[TypedRef, ...] = Field(default_factory=tuple)
    invalidates: tuple[TypedRef, ...] = Field(default_factory=tuple)
    depends_on: tuple[TypedRef, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True}


# -----------------------------
# Core MVP objects
# -----------------------------

class AtomSpec(BaseModel):
    """Leaf experiment spec. Only Atom can reach L2/L3."""

    atom_id: str
    atom_kind: str  # e.g. "rabi.amplitude"
    atom_version: str
    target: TargetSpec
    scan: ScanSpec
    acquisition: AcquisitionSpec
    capability_requirements: tuple[str, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True}


class ExperimentSpec(BaseModel):
    """Top-level envelope for L1 experiment specification (recursive for future Task/Session)."""

    schema_version: str = "qxtrl.el.ExperimentSpec/v0.1"
    spec_id: str
    display_name: Optional[str] = None
    node_kind: Literal["atom", "task", "session"] = "atom"
    atom: Optional[AtomSpec] = None
    children: tuple["ExperimentSpec", ...] = Field(default_factory=tuple)
    pdca_path: tuple[PDCAPathItem, ...]
    l0_context: L0ContextRef
    plan: PlanSpec
    do: DoSpec
    check: CheckSpec
    act: ActSpec
    io: NodeIOContract
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _mvp_restrictions_and_l0_gate(self) -> ExperimentSpec:
        if self.node_kind != "atom":
            raise QXtrlValidationError("MVP only supports node_kind='atom'", rule="L1-MVP-ATOM")
        if self.children:
            raise QXtrlValidationError("MVP Atom must not have children", rule="L1-MVP-CHILDREN")
        if self.atom is None:
            raise QXtrlValidationError("MVP Atom requires 'atom' field", rule="L1-MVP-ATOM")

        # Schema version MUST be exactly the MVP version (no prefix match, no future minor)
        if self.schema_version != "qxtrl.el.ExperimentSpec/v0.1":
            raise QXtrlValidationError(
                f"schema_version must be exactly 'qxtrl.el.ExperimentSpec/v0.1', got {self.schema_version}",
                field="schema_version",
                rule="L1-SCHEMA-VERSION",
            )

        # Full L0 gate calls for physical/control path (complete integration)
        # If the context refs are actual L0 model instances (not just str refs), call the gate.
        # This enforces the "physical/control path must pass L0 gates" rule.
        l0_refs = [
            ("chip_model", self.l0_context.chip_model_ref),
            ("wiring_graph", self.l0_context.wiring_graph_ref),
            ("hardware_inventory", self.l0_context.hardware_inventory_ref),
            ("safety_policy", self.l0_context.safety_policy_ref),
        ]
        for name, ref in l0_refs:
            if ref is not None and hasattr(ref, "require_usable_for_control"):
                try:
                    ref.require_usable_for_control(context=f"l1.validate.{name}")
                except Exception as e:
                    # Re-raise as L1 error for clarity, but preserve original
                    raise QXtrlValidationError(
                        f"L0 {name} context did not pass usable_for_control gate: {e}",
                        field=f"l0_context.{name}",
                        rule="L1-L0-GATE",
                    ) from e

        # Additional negative rules from design doc (more strictness)
        if self.plan is None or self.do is None or self.check is None or self.act is None:
            raise QXtrlValidationError("Atom requires plan, do, check, act", rule="L1-MVP-PDCA")

        # io basic declaration
        if not self.io.consumes or not self.io.produces:
            raise QXtrlValidationError("io must declare consumes and produces", rule="L1-IO")

        # target consistency with plan (MVP)
        if self.atom and self.plan:
            if self.atom.target.element_id != self.plan.target.element_id:
                raise QXtrlValidationError(
                    "atom.target and plan.target element_id must match",
                    rule="L1-TARGET-CONSISTENCY",
                )

        # parameter_ref calibration element consistency (MVP rule)
        target_elem = self.plan.target.element_id if self.plan else None
        if target_elem:
            # scan axes
            for ax in (self.plan.scan.axes if self.plan and self.plan.scan else []):
                pr = ax.parameter_ref
                if pr.startswith("calibration."):
                    elem = pr.split(".")[1]
                    if elem != target_elem:
                        raise QXtrlValidationError(
                            f"calibration parameter_ref element_id '{elem}' must match target '{target_elem}'",
                            field="plan.scan.axes[].parameter_ref",
                            rule="L1-PARAM-REF-TARGET",
                        )
            # act proposals
            for pt in (self.act.proposal_targets if self.act else []):
                pr = pt.parameter_ref
                if pr.startswith("calibration."):
                    elem = pr.split(".")[1]
                    if elem != target_elem:
                        raise QXtrlValidationError(
                            f"proposal parameter_ref element_id '{elem}' must match target '{target_elem}'",
                            field="act.proposal_targets[].parameter_ref",
                            rule="L1-PARAM-REF-TARGET",
                        )

        return self

    # Contract models are immutable after validation (prevents failed assignment and
    # post-validation mutation from leaving a "validated" object in illegal state).
    # IMPORTANT: Do NOT use bare .model_copy(update=...) for evolution — it skips re-validation.
    # Always use validated_copy(...) or ExperimentSpec.model_validate(...) to ensure the result is fully validated.
    model_config = {"frozen": True}

    def validated_copy(self, **updates: Any) -> "ExperimentSpec":
        """Return a new validated ExperimentSpec with updates applied.
        This forces full model_validate so that all L1 + L0 rules are re-applied.
        """
        data = self.model_dump()
        data.update(updates)
        return ExperimentSpec.model_validate(data)

    # Additional L0 gate enforcement can be called explicitly for physical paths
    # (the after validator already does it for object refs)


# Rebuild for recursion
ExperimentSpec.model_rebuild()


class RegistryEntry(BaseModel):
    """Minimal registry entry for templates (Atom, Analyzer, ...)."""

    entry_id: str
    entry_kind: Literal["atom", "analyzer", "optimizer", "backend", "storage"]
    version: str
    display_name: Optional[str] = None
    input_schema: str
    output_schema: str
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    compatible_l1_versions: tuple[str, ...]
    io_contract_template: Optional[NodeIOContract] = None

    model_config = {"frozen": True}


# -----------------------------
# Simple in-memory Registry for MVP
# -----------------------------

class _SimpleRegistry:
    def __init__(self):
        self._entries: dict[str, RegistryEntry] = {}

    def register(self, entry: RegistryEntry):
        self._entries[entry.entry_id] = entry

    def resolve(self, entry_id: str, l1_version: str) -> RegistryEntry:
        entry = self._entries.get(entry_id)
        if not entry:
            raise QXtrlValidationError(f"Registry entry not found: {entry_id}", rule="L1-REGISTRY")
        if l1_version not in entry.compatible_l1_versions:
            raise QXtrlValidationError(f"Registry entry {entry_id} not compatible with {l1_version}", rule="L1-REGISTRY")
        return entry

# Global minimal registry instance (can be replaced in real usage)
registry = _SimpleRegistry()


# -----------------------------
# MVP Helper: create Rabi ExperimentSpec
# -----------------------------

def create_rabi_experiment_spec(
    qubit_id: str = "q000",
    drive_line_id: str = "line.xy.q000",
    readout_line_id: str = "line.ro.rr_q000",
    amplitudes: list[float] = None,
    shots: int = 1024,
    pulse_duration_ns: float = 40.0,
    l0_chip_model_ref: str = "chip.demo_rabi_001",
    l0_wiring_ref: str = "wiring.chip.demo_rabi_001",
    l0_hw_ref: str = "hw.station.demo01",
    l0_safety_ref: str = "safety.station.demo01",
) -> ExperimentSpec:
    """Create a minimal Rabi amplitude scan ExperimentSpec for MVP.
    Follows the example in the design doc.
    """
    if amplitudes is None:
        amplitudes = [0.0, 0.05, 0.10, 0.15, 0.20]

    target = TargetSpec(
        element_id=qubit_id,
        drive_line_id=drive_line_id,
        readout_line_id=readout_line_id,
    )
    amp_values = tuple(float(x) for x in amplitudes) if amplitudes else (0.0, 0.05, 0.10, 0.15, 0.20)
    scan = ScanSpec(
        axes=(ScanAxisSpec(
            axis_id="amp",
            parameter_ref="pulse.drive.amplitude",
            unit="a.u.",
            values=amp_values,
        ),)
    )
    acquisition = AcquisitionSpec(shots=shots)

    plan = PlanSpec(
        objective="estimate_pi_amp",
        target=target,
        scan=scan,
        acquisition=acquisition,
    )

    do = DoSpec(
        atom_ref="qxtrl.atom.rabi_amplitude/v0.1",
        pulse_template_ref="qxtrl.pulse.rabi_gaussian/v0.1",
        parameters={"pulse_duration": Quantity(value=pulse_duration_ns, unit="ns")},
        compile_hints={"frame_policy": "use_l0_defaults"},
    )

    check = CheckSpec(
        analyzer_ref="qxtrl.check.rabi_fit/v0.1",
        expected_observation="rabi_curve",
        metrics=("pi_amp", "contrast", "fit_quality"),
        acceptance={"min_fit_quality": 0.95, "min_contrast": 0.1},
    )

    act = ActSpec(
        mode="propose_patch",
        requires_review=True,
        proposal_targets=(ParameterProposalTarget(
            parameter_ref=f"calibration.{qubit_id}.xy.pi_amp",
            source_metric="pi_amp",
        ),),
    )

    io = NodeIOContract(
        consumes=(
            TypedRef(kind="qubit", ref=qubit_id),
            TypedRef(kind="line", ref=drive_line_id),
            TypedRef(kind="line", ref=readout_line_id),
        ),
        produces=(
            TypedRef(kind="observation", ref="observation.rabi_curve"),
            TypedRef(kind="proposal", ref=f"proposal.{qubit_id}.pi_amp"),
        ),
    )

    pdca_path = (PDCAPathItem(
        node_id=f"atom.rabi.{qubit_id}",
        node_kind="atom",
        pdca_phase="do",
        iteration=0,
    ),)

    l0_context = L0ContextRef(
        chip_model_ref=l0_chip_model_ref,
        wiring_graph_ref=l0_wiring_ref,
        hardware_inventory_ref=l0_hw_ref,
        safety_policy_ref=l0_safety_ref,
    )

    atom = AtomSpec(
        atom_id=f"atom.rabi.{qubit_id}",
        atom_kind="rabi.amplitude",
        atom_version="v0.1",
        target=target,
        scan=scan,
        acquisition=acquisition,
        capability_requirements=("drive_iq", "readout_adc"),
    )

    return ExperimentSpec(
        spec_id=f"exp.rabi.{qubit_id}.amp_scan",
        display_name=f"Rabi amplitude scan on {qubit_id}",
        node_kind="atom",
        atom=atom,
        pdca_path=pdca_path,
        l0_context=l0_context,
        plan=plan,
        do=do,
        check=check,
        act=act,
        io=io,
    )


def create_time_rabi_experiment_spec(
    qubit_id: str = "q001",
    drive_line_id: str = None,
    readout_line_id: str = None,
    durations: list[float] = None,
    fixed_amplitude: float = 0.1,
    shots: int = 1024,
    l0_chip_model_ref: str = "chip.demo_rabi_001",
    l0_wiring_ref: str = "wiring.chip.demo_rabi_001",
    l0_hw_ref: str = "hw.station.demo01",
    l0_safety_ref: str = "safety.station.demo01",
) -> ExperimentSpec:
    """Create a time-Rabi (duration scan at fixed amplitude) ExperimentSpec.

    This matches the user's rehearsal story:
    - Specific qubit (e.g. q001)
    - Fixed amplitude on its control (drive) line
    - Scan pulse width (duration)
    - Readout after the pulse
    """
    if drive_line_id is None:
        drive_line_id = f"line.xy.{qubit_id}"
    if readout_line_id is None:
        readout_line_id = f"line.ro.rr_{qubit_id}"

    if durations is None:
        durations = [10.0, 20.0, 30.0, 40.0, 50.0, 80.0, 120.0]  # ns

    target = TargetSpec(
        element_id=qubit_id,
        drive_line_id=drive_line_id,
        readout_line_id=readout_line_id,
    )

    dur_values = tuple(float(x) for x in durations)
    scan = ScanSpec(
        axes=(ScanAxisSpec(
            axis_id="dur",
            parameter_ref="pulse.drive.duration",
            unit="ns",
            values=dur_values,
        ),)
    )
    acquisition = AcquisitionSpec(shots=shots)

    plan = PlanSpec(
        objective="characterize_rabi_vs_time",
        target=target,
        scan=scan,
        acquisition=acquisition,
    )

    do = DoSpec(
        atom_ref="qxtrl.atom.rabi_duration/v0.1",
        pulse_template_ref="qxtrl.pulse.rabi_gaussian/v0.1",
        parameters={"pulse_amplitude": Quantity(value=fixed_amplitude, unit="a.u.")},
        compile_hints={"frame_policy": "use_l0_defaults"},
    )

    check = CheckSpec(
        analyzer_ref="qxtrl.check.rabi_fit/v0.1",
        expected_observation="rabi_curve_vs_time",
        metrics=("oscillation_period", "decay", "contrast"),
        acceptance={"min_contrast": 0.05},
    )

    act = ActSpec(
        mode="propose_patch",
        requires_review=True,
        proposal_targets=(ParameterProposalTarget(
            parameter_ref=f"calibration.{qubit_id}.xy.drive_strength",
            source_metric="oscillation_period",
        ),),
    )

    io = NodeIOContract(
        consumes=(
            TypedRef(kind="qubit", ref=qubit_id),
            TypedRef(kind="line", ref=drive_line_id),
            TypedRef(kind="line", ref=readout_line_id),
        ),
        produces=(
            TypedRef(kind="observation", ref="observation.rabi_curve_vs_time"),
            TypedRef(kind="proposal", ref=f"proposal.{qubit_id}.drive_strength"),
        ),
    )

    pdca_path = (PDCAPathItem(
        node_id=f"atom.time_rabi.{qubit_id}",
        node_kind="atom",
        pdca_phase="do",
        iteration=0,
    ),)

    l0_context = L0ContextRef(
        chip_model_ref=l0_chip_model_ref,
        wiring_graph_ref=l0_wiring_ref,
        hardware_inventory_ref=l0_hw_ref,
        safety_policy_ref=l0_safety_ref,
    )

    atom = AtomSpec(
        atom_id=f"atom.time_rabi.{qubit_id}",
        atom_kind="rabi.duration",
        atom_version="v0.1",
        target=target,
        scan=scan,
        acquisition=acquisition,
        capability_requirements=("drive_iq", "readout_adc"),
    )

    return ExperimentSpec(
        spec_id=f"exp.rabi.{qubit_id}.time_scan",
        display_name=f"Time Rabi (duration scan) on {qubit_id} at amp={fixed_amplitude}",
        node_kind="atom",
        atom=atom,
        pdca_path=pdca_path,
        l0_context=l0_context,
        plan=plan,
        do=do,
        check=check,
        act=act,
        io=io,
    )


# Register default Rabi atom and analyzer for MVP
registry.register(RegistryEntry(
    entry_id="qxtrl.atom.rabi_amplitude/v0.1",
    entry_kind="atom",
    version="v0.1",
    input_schema="qxtrl.el.AtomSpec.rabi_amplitude/v0.1",
    output_schema="qxtrl.cpir.PulseIR.rabi_amplitude_input/v0.1",
    capabilities=("drive_iq", "readout_adc"),
    compatible_l1_versions=("qxtrl.el.ExperimentSpec/v0.1",),
))

registry.register(RegistryEntry(
    entry_id="qxtrl.check.rabi_fit/v0.1",
    entry_kind="analyzer",
    version="v0.1",
    input_schema="qxtrl.el.Observation.rabi_curve/v0.1",  # short code per naming rules
    output_schema="qxtrl.co.Observation.rabi_fit/v0.1",   # L6/CO short code (temporary until full CO schema)
    capabilities=(),
    compatible_l1_versions=("qxtrl.el.ExperimentSpec/v0.1",),
))
