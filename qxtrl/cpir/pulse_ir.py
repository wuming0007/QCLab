"""L2 / CPIR Pulse IR models (Pydantic, following QXtrl_L2_CPIR_Compiler_PulseIR_设计.md v0.2).

Stable schema prefix: qxtrl.cpir.*
MVP focuses on structured Sweep + template moments (no final waveform arrays in contract).
"""

from __future__ import annotations

import math
from typing import Any, Literal, Optional
import types

from pydantic import BaseModel, Field, model_validator, field_validator

# L0SnapshotRef available from qxtrl.cc when stronger typing is needed

# Forbidden keys for no-waveform guard (recursively)
_WAVEFORM_FORBIDDEN = {"waveform", "waveforms", "samples", "iq_array", "dac_samples", "adc_samples", "ndarray", "raw_data"}


def _contains_forbidden(obj: Any) -> bool:
    """Recursive check for forbidden waveform keys in dicts/lists."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in _WAVEFORM_FORBIDDEN or _contains_forbidden(v):
                return True
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            if _contains_forbidden(item):
                return True
    return False


def _validate_numeric_non_negative(v: float, field: str) -> float:
    if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
        raise ValueError(f"{field} must be finite non-negative number, got {v}")
    return float(v)


def _validate_positive_duration(v: float, field: str) -> float:
    if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v <= 0:
        raise ValueError(f"{field} must be positive finite number, got {v}")
    return float(v)


def _deep_freeze(obj: Any) -> Any:
    """Best-effort deep freeze for dicts/lists to protect post-validation mutation (MVP)."""
    if isinstance(obj, dict):
        return types.MappingProxyType({k: _deep_freeze(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        return tuple(_deep_freeze(v) for v in obj)
    return obj


# -----------------------------
# Sweep (authoritative, not hidden in metadata)
# -----------------------------

class SweepAxis(BaseModel):
    axis_id: str
    parameter_ref: str
    unit: str
    values: tuple[float, ...]

    model_config = {"frozen": True}

    @field_validator("values", mode="before")
    @classmethod
    def _validate_values(cls, v):
        if not v:
            raise ValueError("sweep axis values cannot be empty")
        cleaned = []
        for val in v:
            if isinstance(val, bool):
                raise ValueError("sweep values must not contain bool")
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                raise ValueError("sweep values must not contain NaN/Inf")
            cleaned.append(float(val))
        return tuple(cleaned)

    @field_validator("parameter_ref")
    @classmethod
    def _validate_parameter_ref(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("parameter_ref must be non-empty string")
        # MVP for Rabi at least should look like pulse.drive.xxx or calibration...
        # but keep minimal for now
        return v


class SweepSpec(BaseModel):
    axes: tuple[SweepAxis, ...]
    mode: Literal["grid", "zip"] = "grid"
    order: Literal["as_declared", "randomized"] = "as_declared"
    seed: Optional[int] = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_sweep_mvp(self) -> "SweepSpec":
        if len(self.axes) == 0:
            raise ValueError("SweepSpec must have at least one axis for MVP")
        if self.order == "randomized":
            # MVP currently does not support randomized; enforce per design
            raise ValueError("Rabi MVP does not support randomized order yet")
        return self


# -----------------------------
# Core IR elements
# -----------------------------

class PulseMoment(BaseModel):
    """Template moment. Sweep bindings instead of expanded values."""
    moment_id: str
    kind: Literal["drive", "readout", "wait", "barrier", "acquire"]
    line_id: str
    t0_ns: float
    duration_ns: float
    template_ref: Optional[str] = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    sweep_bindings: dict[str, str] = Field(default_factory=dict)  # e.g. {"amplitude": "sweep.axis.amp"}
    frame_id: Optional[str] = None

    model_config = {"frozen": True}

    @field_validator("t0_ns", "duration_ns", mode="before")
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("numeric time/duration fields must not be bool")
        return v

    @model_validator(mode="after")
    def _validate_moment(self) -> "PulseMoment":
        # pure validation (no assign on frozen)
        _validate_numeric_non_negative(self.t0_ns, "t0_ns")
        _validate_positive_duration(self.duration_ns, "duration_ns")

        # Coherent operations require frame binding (MVP rule)
        if self.kind in ("drive", "readout") and not self.frame_id:
            raise ValueError(f"coherent moment kind={self.kind} must have frame_id")

        if _contains_forbidden(self.parameters):
            raise ValueError("PulseMoment.parameters must not contain waveform data at any level")

        if _contains_forbidden(self.sweep_bindings):
            raise ValueError("sweep_bindings must not contain waveform data")

        return self

    def validated_copy(self, **updates: Any) -> "PulseMoment":
        """Return a new validated copy. Always re-validates."""
        data = self.model_dump()
        data.update(updates)
        return PulseMoment.model_validate(data)


class FrameEvent(BaseModel):
    frame_id: str
    line_id: str
    t0_ns: float
    phase_rad: float = 0.0
    frequency_hz: Optional[float] = None

    model_config = {"frozen": True}

    @field_validator("t0_ns", "phase_rad", mode="before")
    @classmethod
    def _reject_bool_numeric(cls, v):
        if isinstance(v, bool):
            raise ValueError("numeric frame time/phase fields must not be bool")
        return v

    @model_validator(mode="after")
    def _validate_frame(self) -> "FrameEvent":
        _validate_numeric_non_negative(self.t0_ns, "t0_ns")
        if self.frequency_hz is not None:
            if not isinstance(self.frequency_hz, (int, float)) or math.isnan(self.frequency_hz) or math.isinf(self.frequency_hz):
                raise ValueError("frequency_hz must be finite or None")
        return self


class AcquireWindow(BaseModel):
    window_id: str
    line_id: str
    t0_ns: float
    duration_ns: float
    result_level: Literal["raw_iq", "integrated_iq", "classified"] = "integrated_iq"
    integration_kernel_ref: Optional[str] = None

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_acquire(self) -> "AcquireWindow":
        _validate_numeric_non_negative(self.t0_ns, "t0_ns")
        _validate_positive_duration(self.duration_ns, "duration_ns")
        return self


class ResourceUsage(BaseModel):
    line_ids: tuple[str, ...] = ()
    estimated_points: int = 0
    estimated_shots: int = 0
    estimated_duration_ns_per_point: float = 0.0

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_resources(self) -> "ResourceUsage":
        if self.estimated_points < 0 or self.estimated_shots < 0:
            raise ValueError("estimated_points and estimated_shots must be non-negative")
        _validate_numeric_non_negative(
            self.estimated_duration_ns_per_point, "estimated_duration_ns_per_point"
        )
        return self


class PulseIR(BaseModel):
    """Hardware-agnostic pulse IR. Stable contract target uses Pydantic + schema_version."""
    schema_version: Literal["qxtrl.cpir.PulseIR/v0.1"] = "qxtrl.cpir.PulseIR/v0.1"
    ir_id: str
    source_spec_id: str
    atom_id: str
    target: dict[str, Any] = Field(default_factory=dict)
    sweep: SweepSpec
    moments: tuple[PulseMoment, ...] = ()
    frames: tuple[FrameEvent, ...] = ()
    acquisition_windows: tuple[AcquireWindow, ...] = ()
    resources: ResourceUsage = Field(default_factory=ResourceUsage)
    total_duration_ns: float
    content_hash: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)  # for transition / diagnostics only

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_pulseir_contract(self) -> "PulseIR":
        # 1. Sweep MVP constraints (exactly one axis, specific ref for Rabi)
        if len(self.sweep.axes) != 1:
            raise ValueError("Rabi MVP requires exactly one sweep axis")
        ax = self.sweep.axes[0]
        if ax.parameter_ref not in ("pulse.drive.amplitude", "pulse.drive.duration"):
            raise ValueError(f"Rabi MVP only supports pulse.drive.amplitude or .duration, got {ax.parameter_ref}")

        # 2. Waveform guards on open dicts
        if _contains_forbidden(self.target):
            raise ValueError("PulseIR.target must not contain waveform data")
        if _contains_forbidden(self.metadata):
            raise ValueError("PulseIR.metadata must not contain waveform data")

        # 3. Time coverage
        _validate_positive_duration(self.total_duration_ns, "total_duration_ns")
        for m in self.moments:
            if m.t0_ns + m.duration_ns > self.total_duration_ns + 1e-9:
                raise ValueError("moment extends beyond total_duration_ns")
        for w in self.acquisition_windows:
            if w.t0_ns + w.duration_ns > self.total_duration_ns + 1e-9:
                raise ValueError("acquire window extends beyond total_duration_ns")

        # 4. Frame consistency (core P0)
        frame_map = {f.frame_id: f for f in self.frames}
        if len(frame_map) != len(self.frames):
            raise ValueError("frame_id must be unique within PulseIR.frames")

        for m in self.moments:
            if m.kind in ("drive", "readout"):
                if not m.frame_id:
                    raise ValueError(f"coherent moment {m.moment_id} missing frame_id")
                if m.frame_id not in frame_map:
                    raise ValueError(f"moment {m.moment_id} references unknown frame_id {m.frame_id}")
                f = frame_map[m.frame_id]
                if f.line_id != m.line_id:
                    raise ValueError(f"moment {m.moment_id} line_id {m.line_id} mismatches its frame line_id {f.line_id}")
                if f.t0_ns > m.t0_ns + 1e-9:
                    raise ValueError(f"frame event for {m.frame_id} starts after moment t0")

        # Frame events per line monotonic (simple check)
        events_by_line: dict[str, list[FrameEvent]] = {}
        for f in self.frames:
            events_by_line.setdefault(f.line_id, []).append(f)
        for line, evs in events_by_line.items():
            times = [e.t0_ns for e in evs]
            if times != sorted(times):
                raise ValueError(f"frame events for line {line} not monotonic in t0_ns")

        return self

    def validated_copy(self, **updates: Any) -> "PulseIR":
        """Return a new validated PulseIR. Re-runs all validators."""
        data = self.model_dump()
        data.update(updates)
        return PulseIR.model_validate(data)


# -----------------------------
# Bundle and Diagnostics (MVP targets)
# -----------------------------

class CompileDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.cpir.CompileDiagnostic/v0.1"] = "qxtrl.cpir.CompileDiagnostic/v0.1"
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    path: Optional[str] = None
    hint: Optional[str] = None

    model_config = {"frozen": True}


class CompiledBundle(BaseModel):
    schema_version: Literal["qxtrl.cpir.CompiledBundle/v0.1"] = "qxtrl.cpir.CompiledBundle/v0.1"
    bundle_id: str
    pulse_ir: PulseIR
    diagnostics: tuple[CompileDiagnostic, ...] = ()
    l0_refs: tuple[str, ...] = ()  # str refs or snapshot ids for MVP traceability
    source_spec_id: str
    source_spec_hash: str
    compiler_version: str = "0.2-mvp"
    bundle_hash: Optional[str] = None

    model_config = {"frozen": True}

    def validated_copy(self, **updates: Any) -> "CompiledBundle":
        data = self.model_dump()
        data.update(updates)
        return CompiledBundle.model_validate(data)
