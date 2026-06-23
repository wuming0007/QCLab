"""Minimal L3/EB models for MVP (aligns with QXtrl_L3_EB_ExecutionBackend_设计.md)."""

from __future__ import annotations

from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, field_validator, model_validator
import math
from types import FunctionType, MethodType

# Re-export / import from L2 for bundle
from qxtrl.cpir import CompiledBundle


class BackendSubmitRequest(BaseModel):
    schema_version: Literal["qxtrl.eb.BackendSubmitRequest/v0.1"] = "qxtrl.eb.BackendSubmitRequest/v0.1"
    request_id: str
    run_id: str
    backend_id: str
    bundle: CompiledBundle
    mode: Literal["dry_run", "virtual", "replay", "hardware"] = "virtual"
    timeout_s: float = 60.0
    options: dict[str, Any] = {}

    model_config = {"frozen": True}

    @field_validator("timeout_s")
    @classmethod
    def _validate_timeout(cls, v: float) -> float:
        if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v <= 0:
            raise ValueError("timeout_s must be positive finite number")
        return float(v)

    @model_validator(mode="after")
    def _validate_options(self) -> "BackendSubmitRequest":
        def _has_callable(o):
            if isinstance(o, (FunctionType, MethodType)) or callable(o) and not isinstance(o, (str, int, float, bool, type(None), list, dict, tuple)):
                # rough check for non-primitive callable
                if not isinstance(o, (str, bytes, int, float, complex, bool, type(None), list, dict, tuple, set)):
                    try:
                        if callable(o):
                            return True
                    except Exception:
                        pass
            if isinstance(o, dict):
                return any(_has_callable(v) for v in o.values())
            if isinstance(o, (list, tuple, set)):
                return any(_has_callable(v) for v in o)
            return False
        if _has_callable(self.options):
            raise ValueError("options must not contain callables or non-serializable objects")
        return self

    def validated_copy(self, **updates: Any) -> "BackendSubmitRequest":
        data = self.model_dump()
        data.update(updates)
        return BackendSubmitRequest.model_validate(data)


class BackendCapability(BaseModel):
    schema_version: Literal["qxtrl.eb.BackendCapability/v0.1"] = "qxtrl.eb.BackendCapability/v0.1"
    backend_id: str
    backend_kind: Literal["virtual", "real_hardware", "replay", "hil"]
    supported_bundle_versions: tuple[str, ...]
    supported_result_levels: tuple[str, ...]
    max_points: Optional[int] = None
    supports_cancel: bool = False
    supports_fault_injection: bool = False


class BackendDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.eb.BackendDiagnostic/v0.1"] = "qxtrl.eb.BackendDiagnostic/v0.1"
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    stage: Optional[str] = None
    path: Optional[str] = None
    hint: Optional[str] = None


class BackendEvent(BaseModel):
    schema_version: Literal["qxtrl.eb.BackendEvent/v0.1"] = "qxtrl.eb.BackendEvent/v0.1"
    event_id: str
    run_id: str
    backend_id: str
    stage: Literal[
        "created", "validating", "preparing", "uploading",
        "arming", "running", "acquiring", "completed",
        "failed", "cancelled", "cleanup"
    ]
    state: Literal["started", "succeeded", "failed", "skipped"]
    t_rel_ms: float
    details: dict[str, Any] = {}

    model_config = {"frozen": True}

    @field_validator("t_rel_ms")
    @classmethod
    def _validate_t_rel(cls, v: float) -> float:
        if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
            raise ValueError("t_rel_ms must be non-negative finite number")
        return float(v)


class BackendRunResult(BaseModel):
    schema_version: Literal["qxtrl.eb.BackendRunResult/v0.1"] = "qxtrl.eb.BackendRunResult/v0.1"
    run_id: str
    backend_id: str
    final_state: Literal["succeeded", "failed", "cancelled", "rejected"]
    bundle_id: str
    bundle_hash: str
    pulse_ir_hash: str
    result_level: str
    data: dict[str, Any] = {}
    data_refs: tuple[str, ...] = ()
    events: tuple[BackendEvent, ...] = ()
    diagnostics: tuple[BackendDiagnostic, ...] = ()
    metrics: dict[str, float] = {}

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_result_consistency(self) -> "BackendRunResult":
        if self.final_state == "succeeded":
            if not self.bundle_hash or not self.pulse_ir_hash or not self.result_level:
                raise ValueError("succeeded result must have non-empty bundle_hash, pulse_ir_hash, result_level")
            if not self.events or not any(e.state == "succeeded" and e.stage == "completed" for e in self.events):
                raise ValueError("succeeded result should have at least one completed succeeded event")
        elif self.final_state in ("rejected", "failed"):
            if not any(d.severity == "error" for d in self.diagnostics):
                raise ValueError("rejected/failed result must include at least one error diagnostic")
        return self

    def validated_copy(self, **updates: Any) -> "BackendRunResult":
        data = self.model_dump()
        data.update(updates)
        return BackendRunResult.model_validate(data)


class ExecutionBackend(Protocol):
    """ExecutionBackend Protocol as per design."""

    backend_id: str

    def describe_capability(self) -> BackendCapability:
        ...

    def validate_bundle(self, bundle: CompiledBundle | dict) -> dict[str, Any]:
        """Returns a validation report dict for MVP."""

    def submit(self, request: BackendSubmitRequest | dict) -> BackendRunResult:
        ...

    def cancel(self, run_id: str, reason: str) -> BackendRunResult:
        ...

    def safe_stop(self, reason: str) -> BackendDiagnostic:
        ...
