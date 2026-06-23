"""Core L0 (CC) domain models (pydantic).

Implements:
- HardwareInventory (minimal)
- ChipModel + elements
- WiringGraph + edges
- SafetyPolicy
- Supporting identity / quality / snapshot types

All models enforce L0 naming rules, schema_version, and "missing => deny" policy.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, ClassVar, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator

from .errors import QXtrlValidationError
from .quantity import Quantity
from .validators import (
    validate_channel_id,
    validate_device_id,
    validate_element_id,
    validate_identity_id,
    validate_line_id,
    validate_schema_version,
)


# -----------------------------
# Common governance primitives
# -----------------------------

SourceKind = Literal[
    "public_example",
    "vendor_snapshot",
    "lab_calibrated",
    "simulated",
    "draft",
    "imported",
]

Status = Literal["draft", "approved", "disabled", "retired", "unknown"]


class SourceRef(BaseModel):
    """Pointer to source material for auditability."""

    label: str
    url: Optional[str] = None
    retrieved_date: Optional[str] = None  # YYYY-MM-DD


class DataQuality(BaseModel):
    """Governance & usability metadata. Core of 'missing => deny'.

    This is the single source of truth for whether an L0 object (and the
    resources it describes) may be used for real control/execution.

    - usable_for_control=True is only meaningful when combined with
      status="approved", approved_by, approved_at, and no revocation.
    - Once revoked (revoked_by/revoked_at set), usable_for_control must be False.
    - Mutations that would violate the governance rules are rejected at
      assignment time.
    """

    # Allow documented example values + base set (examples use "public_fact_plus_...")
    confidence: str = "unknown"
    usable_for_control: bool = False
    missing_fields_policy: Literal["deny_physical_execution", "warn", "allow_simulation"] = "deny_physical_execution"
    status: Status = "draft"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None  # ISO8601 UTC

    # Revocation fields for approval revocation mechanism
    revoked_by: Optional[str] = None
    revoked_at: Optional[str] = None  # ISO8601 UTC
    revocation_reason: Optional[str] = None

    model_config = {
        "validate_assignment": True,
        "extra": "forbid",
        "str_strip_whitespace": True,
    }

    @model_validator(mode="after")
    def _enforce_usable(self) -> DataQuality:
        # Revocation takes precedence: if revoked, cannot be usable for control
        if self.revoked_by or self.revoked_at:
            if self.usable_for_control:
                raise QXtrlValidationError(
                    "Cannot have usable_for_control=True when revocation fields are set",
                    field="data_quality",
                    rule="R-REVOCATION",
                )
            # Status should be consistent with revocation (disabled or retired recommended)
            if self.status not in ("disabled", "retired", "unknown"):
                raise QXtrlValidationError(
                    "When revocation fields are set, status should be 'disabled', 'retired' or 'unknown'",
                    field="data_quality",
                    rule="R-REVOCATION",
                )

        if self.usable_for_control:
            if self.status != "approved":
                raise QXtrlValidationError(
                    "usable_for_control=True requires status='approved'",
                    field="data_quality",
                    rule="R-004",
                )
            if not self.approved_by:
                raise QXtrlValidationError(
                    "usable_for_control=True requires approved_by",
                    field="data_quality",
                    rule="R-009",
                )
            if not self.approved_at:
                raise QXtrlValidationError(
                    "usable_for_control=True requires approved_at (ISO8601 UTC)",
                    field="data_quality",
                    rule="R-009",
                )
        if self.status == "approved":
            if not self.approved_by:
                raise QXtrlValidationError(
                    "status='approved' requires approved_by",
                    field="data_quality",
                    rule="R-009",
                )
            if not self.approved_at:
                raise QXtrlValidationError(
                    "status='approved' requires approved_at (ISO8601 UTC)",
                    field="data_quality",
                    rule="R-009",
                )
        return self

    def is_approved_for_control(self) -> bool:
        """Canonical method: the only authoritative way to decide if this
        DataQuality (and the L0 object carrying it) may participate in
        physical / control execution.

        Must satisfy all of:
        - usable_for_control is True
        - status == "approved"
        - approved_by is present
        - approved_at is present
        - NOT revoked (no revoked_by or revoked_at)

        Upper layers (L1+) and helpers MUST use this method (or the
        equivalent in is_usable_for_control) instead of reading
        .usable_for_control directly.
        """
        if self.revoked_by or self.revoked_at:
            return False
        return (
            self.usable_for_control
            and self.status == "approved"
            and bool(self.approved_by)
            and bool(self.approved_at)
        )

    def is_revoked(self) -> bool:
        """Returns True if this approval has been revoked."""
        return bool(self.revoked_by or self.revoked_at)

    def revoke(self, by: str, at: str, reason: Optional[str] = None) -> "DataQuality":
        """Convenience to create a revoked copy (does not mutate self).
        Sets usable_for_control=False, status=disabled, and revocation fields.
        """
        return self.model_copy(update={
            "usable_for_control": False,
            "status": "disabled",
            "revoked_by": by,
            "revoked_at": at,
            "revocation_reason": reason,
        })


class Identity(BaseModel):
    """Stable identity + provenance for any L0 object."""

    id: str
    display_name: str
    vendor: Optional[str] = None
    source_kind: SourceKind = "draft"
    source_refs: list[SourceRef] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _id_stable(cls, v: str) -> str:
        return validate_identity_id(v)


class L0Base(BaseModel):
    """All L0 objects inherit these fields.

    IMPORTANT: Concrete subclasses MUST declare schema_version using a precise
    Literal so that object type and contract version are bound together.
    """

    schema_version: str = Field(..., description="qxtrl.cc.<Name>/v<major>.<minor>")
    identity: Identity
    data_quality: DataQuality = Field(default_factory=DataQuality)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: Optional[str] = None

    # Subclasses should set this for clarity (used by runtime check)
    _EXPECTED_SCHEMA_NAME: ClassVar[str] | None = None

    model_config = {
        "extra": "forbid",
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }

    @field_validator("schema_version")
    @classmethod
    def _validate_sv(cls, v: str) -> str:
        # Basic format validation. Name binding is enforced below + by Literal in subclasses.
        return validate_schema_version(v)

    @model_validator(mode="after")
    def _enforce_schema_version_matches_type(self) -> L0Base:
        """Runtime safety net: the <Name> in schema_version must match the concrete class.

        This prevents ChipModel(schema_version="qxtrl.cc.HardwareInventory/v0.1", ...)
        even if someone bypasses field-level Literal.
        """
        if not self.schema_version:
            return self

        m = re.match(r"^qxtrl\.l0\.([A-Za-z0-9_]+)/v", self.schema_version)
        if m:
            declared_name = m.group(1)
            actual_name = self.__class__.__name__
            if declared_name != actual_name:
                raise QXtrlValidationError(
                    f"schema_version type mismatch: this is a {actual_name} "
                    f"but schema_version declares '{declared_name}'",
                    field="schema_version",
                    rule="L0-SCHEMA-NAME-MISMATCH",
                )
        return self

    @field_validator("data_quality")
    @classmethod
    def _validate_data_quality_gate(cls, v: DataQuality) -> DataQuality:
        """Prevent bypassing the usable_for_control gate by direct assignment of a
        mutated or lax DataQuality object. Re-enforces the core rules.
        """
        if v.revoked_by or v.revoked_at:
            if v.usable_for_control:
                raise QXtrlValidationError(
                    "Cannot assign DataQuality with revocation fields and usable_for_control=True",
                    field="data_quality",
                    rule="R-REVOCATION",
                )
        if v.usable_for_control:
            if v.status != "approved":
                raise QXtrlValidationError(
                    "usable_for_control=True requires status='approved'",
                    field="data_quality",
                    rule="R-004",
                )
            if not v.approved_by:
                raise QXtrlValidationError(
                    "usable_for_control=True requires approved_by",
                    field="data_quality",
                    rule="R-009",
                )
            if not v.approved_at:
                raise QXtrlValidationError(
                    "usable_for_control=True requires approved_at",
                    field="data_quality",
                    rule="R-009",
                )
        return v

    def require_usable_for_control(self, *, context: str = "run") -> None:
        """Raise if this object is not safe for physical/control use.

        Delegates to the canonical DataQuality.is_approved_for_control()
        so that status, approval and other governance rules are always respected.
        """
        if not self.data_quality.is_approved_for_control():
            raise QXtrlValidationError(
                f"{self.identity.id} is not approved for control (context={context})",
                field="data_quality",
                rule="R-005",
                status=self.data_quality.status,
                usable_for_control=self.data_quality.usable_for_control,
                approved_by=self.data_quality.approved_by,
            )


# -----------------------------
# Quantity helper (inline in other models)
# -----------------------------

QuantityField = Quantity  # alias for clarity in other models


# -----------------------------
# Chip elements (L0 minimal for Rabi)
# -----------------------------

class QubitElement(BaseModel):
    element_id: str
    display_name: Optional[str] = None
    role: Literal["physical_qubit", "logical"] = "physical_qubit"
    frequency: Optional[Quantity] = None
    anharmonicity: Optional[Quantity] = None
    t1: Optional[Quantity] = None
    t2: Optional[Quantity] = None

    @field_validator("element_id")
    @classmethod
    def _validate(cls, v: str) -> str:
        return validate_element_id(v)


class ResonatorElement(BaseModel):
    element_id: str
    attached_to: str  # qubit id
    frequency: Optional[Quantity] = None

    @field_validator("element_id")
    @classmethod
    def _validate(cls, v: str) -> str:
        return validate_element_id(v)


class CouplerElement(BaseModel):
    element_id: str
    endpoints: list[str]

    @field_validator("element_id")
    @classmethod
    def _validate(cls, v: str) -> str:
        return validate_element_id(v)

    @field_validator("endpoints")
    @classmethod
    def _sorted_endpoints(cls, v: list[str]) -> list[str]:
        if len(v) != 2:
            raise QXtrlValidationError("coupler endpoints must be exactly two qubits", field="endpoints")
        if v[0] > v[1]:
            raise QXtrlValidationError("coupler endpoints must be sorted", field="endpoints", rule="R-coupler-order")
        return v


class ChipModel(L0Base):
    """Static chip topology and properties (frequency etc. are calibration, not identity)."""

    schema_version: Literal["qxtrl.cc.ChipModel/v0.1"] = "qxtrl.cc.ChipModel/v0.1"
    qubits: list[QubitElement] = Field(default_factory=list)
    resonators: list[ResonatorElement] = Field(default_factory=list)
    couplers: list[CouplerElement] = Field(default_factory=list)

    modality: Literal["superconducting", "other"] = "superconducting"
    physical_qubit_count: int = 0

    @model_validator(mode="after")
    def _count_and_ids(self) -> ChipModel:
        # Use object.__setattr__ to avoid recursion when validate_assignment=True
        object.__setattr__(self, "physical_qubit_count", len(self.qubits))
        # Enforce unique element ids
        ids = [q.element_id for q in self.qubits]
        if len(ids) != len(set(ids)):
            raise QXtrlValidationError("duplicate qubit element_id", rule="R-001-unique")
        return self

    @model_validator(mode="after")
    def _validate_topology_consistency(self) -> ChipModel:
        """Enforce basic resonator/coupler topology consistency with qubits.

        - resonator.attached_to must refer to an existing qubit
        - coupler endpoints must refer to existing qubits (already sorted by CouplerElement)
        """
        qubit_ids = {q.element_id for q in self.qubits}
        for res in self.resonators:
            if res.attached_to not in qubit_ids:
                raise QXtrlValidationError(
                    f"resonator {res.element_id} attached_to '{res.attached_to}' is not a known qubit",
                    field="resonators",
                    rule="R-TOPOLOGY-CONSISTENCY",
                )
        for cou in self.couplers:
            for end in cou.endpoints:
                if end not in qubit_ids:
                    raise QXtrlValidationError(
                        f"coupler {cou.element_id} endpoint '{end}' is not a known qubit",
                        field="couplers",
                        rule="R-TOPOLOGY-CONSISTENCY",
                    )
        return self

    def get_qubit(self, qid: str) -> QubitElement:
        for q in self.qubits:
            if q.element_id == qid:
                return q
        raise KeyError(f"qubit {qid} not in ChipModel {self.identity.id}")


# -----------------------------
# Wiring - structured endpoint types (P0-003)
# -----------------------------

class HardwareChannels(BaseModel):
    """Structured hardware channel mapping for a logical line.

    At least one relevant channel should be present for the role.
    Channel IDs must pass L0 channel validation when provided.
    """
    i: Optional[str] = None      # I component for IQ
    q: Optional[str] = None      # Q component for IQ
    adc: Optional[str] = None    # for readout
    marker: Optional[str] = None
    lo: Optional[str] = None
    other: dict[str, str] = Field(default_factory=dict)  # extensibility for other ports

    @model_validator(mode="after")
    def _validate_channel_ids(self) -> HardwareChannels:
        for field_name, ch_id in [
            ("i", self.i),
            ("q", self.q),
            ("adc", self.adc),
            ("marker", self.marker),
            ("lo", self.lo),
        ]:
            if ch_id is not None:
                validate_channel_id(ch_id)
        for ch_id in self.other.values():
            if ch_id:
                validate_channel_id(ch_id)
        return self


class WiringEndpoint(BaseModel):
    """Structured endpoint for a WiringEdge."""
    chip_element: str
    hardware_channels: HardwareChannels = Field(default_factory=HardwareChannels)

    @field_validator("chip_element")
    @classmethod
    def _validate_chip_element(cls, v: str) -> str:
        # chip_element should follow element naming (qNNN, rr_*, etc). Use element validator.
        return validate_element_id(v)


# -----------------------------
# Wiring
# -----------------------------

class WiringEdge(BaseModel):
    """Maps one logical line to one or more hardware channels."""

    line_id: str
    role: str = "drive_iq"  # drive_iq | readout | flux | marker | ...
    # Accept dict for convenience (common in examples/configs) but coerce to typed and validate.
    endpoints: Union[WiringEndpoint, dict[str, Any]]
    signal_chain: list[str] = Field(default_factory=list)  # device order
    status: Status = "draft"
    usable_for_control: bool = False

    @field_validator("line_id")
    @classmethod
    def _line(cls, v: str) -> str:
        return validate_line_id(v)

    @field_validator("endpoints", mode="before")
    @classmethod
    def _coerce_endpoints(cls, v: Any) -> Any:
        if isinstance(v, dict):
            # Coerce and let WiringEndpoint validator run (will validate chip_element + channels)
            return WiringEndpoint.model_validate(v)
        return v

    @model_validator(mode="after")
    def _validate_role_channel_semantics(self) -> WiringEdge:
        """Enforce minimal role / channel semantics for WiringEdge.

        This provides the "minimum semantics" contract so that L2 compiler
        and L3 backends receive sane resource bindings.
        """
        ep = self.endpoints
        if isinstance(ep, dict):
            # Should have been coerced already, but be defensive
            ep = WiringEndpoint.model_validate(ep)

        hc = ep.hardware_channels
        role = self.role

        if role == "drive_iq":
            if not (hc.i and hc.q):
                raise QXtrlValidationError(
                    f"role '{role}' requires both 'i' and 'q' hardware channels",
                    field="endpoints.hardware_channels",
                    rule="R-ROLE-CHANNEL-SEMANTICS",
                )
        elif role == "readout":
            if not hc.adc:
                raise QXtrlValidationError(
                    f"role '{role}' requires 'adc' hardware channel",
                    field="endpoints.hardware_channels",
                    rule="R-ROLE-CHANNEL-SEMANTICS",
                )
        elif role in ("flux", "z", "marker", "lo", "pump", "trig"):
            # For these roles at least one explicit channel or 'other' must be present
            has_any = bool(hc.i or hc.q or hc.adc or hc.marker or hc.lo or hc.other)
            if not has_any:
                raise QXtrlValidationError(
                    f"role '{role}' must declare at least one hardware channel",
                    field="endpoints.hardware_channels",
                    rule="R-ROLE-CHANNEL-SEMANTICS",
                )
        # unknown roles are allowed for extensibility but will have no extra check
        return self


class WiringGraph(L0Base):
    """Logical control/readout resources to physical wiring."""

    schema_version: Literal["qxtrl.cc.WiringGraph/v0.1"] = "qxtrl.cc.WiringGraph/v0.1"
    edges: list[WiringEdge] = Field(default_factory=list)
    resource_groups: dict[str, Any] = Field(default_factory=dict)  # minimal placeholder for MVP

    @model_validator(mode="after")
    def _check_lines(self) -> WiringGraph:
        for e in self.edges:
            if e.usable_for_control and e.status != "approved":
                raise QXtrlValidationError(
                    f"edge {e.line_id} usable_for_control requires approved status",
                    field="edges",
                    rule="R-005",
                )
        return self

    def get_edge(self, line_id: str) -> WiringEdge:
        for e in self.edges:
            if e.line_id == line_id:
                return e
        raise KeyError(f"line {line_id} not in WiringGraph")


# -----------------------------
# Hardware inventory (devices & channels)
# -----------------------------

class ChannelCapability(BaseModel):
    signal_kind: Literal["analog_iq", "analog_real", "marker", "trigger", "dc", "adc_input", "unknown"] = "unknown"
    sample_rate: Optional[Quantity] = None
    amplitude_range: Optional[dict[str, Any]] = None  # {min, max, unit}
    timing_resolution: Optional[Quantity] = None
    supports_waveform_upload: bool = False


class Channel(BaseModel):
    channel_id: str
    capabilities: ChannelCapability = Field(default_factory=ChannelCapability)
    safety_limits_ref: Optional[str] = None  # ref to policy entry

    @field_validator("channel_id")
    @classmethod
    def _chan(cls, v: str) -> str:
        return validate_channel_id(v)


class Device(BaseModel):
    device_id: str
    device_type: str
    asset_id: Optional[str] = None  # physical serial vs installation position
    vendor: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    connection: dict[str, Any] = Field(default_factory=dict)
    status: Status = "draft"

    @field_validator("device_id")
    @classmethod
    def _dev(cls, v: str) -> str:
        return validate_device_id(v)


class HardwareInventory(L0Base):
    """Declared instruments, firmware, capabilities (not live state).

    When data_quality.usable_for_control=True, at least one Channel must be
    declared (even for virtual/demo setups, representative channels should be
    provided so that L2/L3 can perform resource binding and safety checks).
    """

    schema_version: Literal["qxtrl.cc.HardwareInventory/v0.1"] = "qxtrl.cc.HardwareInventory/v0.1"
    devices: list[Device] = Field(default_factory=list)
    channels: list[Channel] = Field(default_factory=list)

    @model_validator(mode="after")
    def _require_for_physical(self) -> HardwareInventory:
        if self.data_quality.usable_for_control:
            if not self.devices:
                raise QXtrlValidationError("HardwareInventory usable_for_control but no devices declared", rule="R-005")
            # For usable_for_control=True we expect at least basic channel declarations for resource binding.
            # Virtual/demo cases should still provide representative channels (even if virtual).
            if not self.channels:
                raise QXtrlValidationError(
                    "HardwareInventory with usable_for_control=True must declare at least one channel "
                    "(use representative virtual channels for demo; physical control requires real capability metadata).",
                    rule="R-005",
                )
        return self


# -----------------------------
# Safety policy (deny by default)
# -----------------------------

class SafetyPolicy(L0Base):
    """Site / station safety boundaries. Real execution always takes the strictest of cap/safety/cal."""

    schema_version: Literal["qxtrl.cc.SafetyPolicy/v0.1"] = "qxtrl.cc.SafetyPolicy/v0.1"
    policy_mode: Literal["deny_by_default", "allow_list"] = "deny_by_default"
    applies_to: dict[str, str] = Field(default_factory=dict)  # processor_ref, wiring_graph_ref etc.
    global_rules: dict[str, Any] = Field(
        default_factory=lambda: {
            "require_authenticated_operator": True,
            "require_approved_hardware_inventory": True,
            "require_approved_wiring_graph": True,
            "require_active_calibration_snapshot": True,
            "deny_when_any_required_limit_unknown": True,
            "allow_ai_to_execute_physical_actions": False,
        }
    )
    channel_limits: dict[str, Any] = Field(default_factory=dict)
    operation_classes: dict[str, Any] = Field(default_factory=dict)  # empty by default; use is_operation_allowed which defaults to False (missing => deny)

    @model_validator(mode="after")
    def _enforce_deny_default(self) -> SafetyPolicy:
        # For deny_by_default, we rely on is_operation_allowed to default to False for missing entries.
        # This validator can be extended later for more static policy analysis.
        return self

    def is_operation_allowed(self, op_class: str) -> bool:
        """Return whether a given operation class is explicitly allowed.

        Per L0 "missing => deny" rule: if the key is absent or "allowed" is not true,
        the operation is denied. This applies especially under policy_mode="deny_by_default".
        """
        entry = self.operation_classes.get(op_class, {})
        return bool(entry.get("allowed", False))

    def allows_simulation(self) -> bool:
        return self.is_operation_allowed("simulation")

    def allows_replay(self) -> bool:
        return self.is_operation_allowed("replay")


# -----------------------------
# Snapshot reference (used by RunManifest etc.)
# -----------------------------

class L0SnapshotRef(BaseModel):
    """Immutable reference to a published L0 bundle/snapshot used by a run."""

    snapshot_id: str
    schema_version: str
    content_hash: str  # sha256:...
    generated_at: str
    kind: Literal["hardware_inventory", "wiring_graph", "chip_model", "safety_policy", "calibration", "cc_bundle"]

    @field_validator("schema_version")
    @classmethod
    def _sv(cls, v: str) -> str:
        return validate_schema_version(v)
