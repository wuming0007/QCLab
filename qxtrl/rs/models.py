"""L4/RS Pydantic models per QXtrl_L4_RS_RuntimeScheduler_设计.md."""

from __future__ import annotations

import math
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# Cross-layer imports
from qxtrl.el.models import ExperimentSpec
from qxtrl.eb.models import BackendRunResult  # for embedding in result


class RetryPolicy(BaseModel):
    schema_version: Literal["qxtrl.rs.RetryPolicy/v0.1"] = "qxtrl.rs.RetryPolicy/v0.1"
    max_attempts: int = 1
    retry_on: tuple[str, ...] = ()
    backoff_ms: float = 0.0

    model_config = {"frozen": True}

    @field_validator("max_attempts", mode="before")
    @classmethod
    def _min_attempts(cls, v: Any) -> int:
        if isinstance(v, bool):
            raise ValueError("max_attempts must be int, not bool")
        if not isinstance(v, int) or v < 1:
            raise ValueError("max_attempts must be >= 1")
        return v

    @field_validator("backoff_ms", mode="before")
    @classmethod
    def _validate_backoff(cls, v: Any) -> float:
        if isinstance(v, bool):
            raise ValueError("backoff_ms must be number, not bool")
        if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
            raise ValueError("backoff_ms must be non-negative finite")
        return float(v)


class RunRequest(BaseModel):
    schema_version: Literal["qxtrl.rs.RunRequest/v0.1"] = "qxtrl.rs.RunRequest/v0.1"
    request_id: str
    run_id: Optional[str] = None
    submitted_by: Optional[str] = None
    experiment_spec: ExperimentSpec | dict[str, Any]
    backend_id: str = "backend.virtual.rabi_mvp"
    mode: Literal["dry_run", "virtual", "replay", "hardware"] = "virtual"
    priority: int = 100
    timeout_s: float = 300.0
    idempotency_key: Optional[str] = None
    tags: dict[str, str] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
    retry_policy: Optional[RetryPolicy] = None

    model_config = {"frozen": True}

    @field_validator("timeout_s", mode="before")
    @classmethod
    def _validate_timeout(cls, v: Any) -> float:
        if isinstance(v, bool):
            raise ValueError("timeout_s must be number, not bool")
        if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v <= 0:
            raise ValueError("timeout_s must be positive finite number")
        return float(v)

    @staticmethod
    def _is_strict_json_like(v: Any) -> bool:
        """Recursive JSON-like: primitives only (no set, object(), NaN, models, callables)."""
        if v is None:
            return True
        if isinstance(v, bool):
            return True
        if isinstance(v, (int, str)):
            return True
        if isinstance(v, float):
            return not (math.isnan(v) or math.isinf(v))
        if isinstance(v, list):
            return all(RunRequest._is_strict_json_like(x) for x in v)
        if isinstance(v, dict):
            return all(
                isinstance(k, (str, int)) and RunRequest._is_strict_json_like(val)
                for k, val in v.items()
            )
        return False

    @model_validator(mode="after")
    def _validate_options_and_tags(self) -> "RunRequest":
        if not self._is_strict_json_like(self.options):
            raise ValueError("options must be strict JSON-like (no sets, custom objects, NaN/Inf, callables)")
        if not self._is_strict_json_like(self.tags):
            raise ValueError("tags must be strict JSON-like")
        return self


class RunReceipt(BaseModel):
    schema_version: Literal["qxtrl.rs.RunReceipt/v0.1"] = "qxtrl.rs.RunReceipt/v0.1"
    request_id: str
    run_id: str
    accepted: bool
    state: Literal["accepted", "rejected"]
    submitted_at_ns: int
    diagnostics: tuple[RuntimeDiagnostic, ...] = ()

    model_config = {"frozen": True}


class RunState(BaseModel):
    schema_version: Literal["qxtrl.rs.RunState/v0.1"] = "qxtrl.rs.RunState/v0.1"
    run_id: str
    request_id: str
    lifecycle_state: Literal[
        "created", "accepted", "queued", "validating", "compiling",
        "waiting_for_resources", "submitting", "running", "analyzing",
        "persisting", "succeeded", "failed", "cancelled", "rejected"
    ]
    backend_id: Optional[str] = None
    mode: str
    current_stage: Optional[str] = None
    progress: Optional[float] = None
    last_event_id: Optional[str] = None
    diagnostics: tuple[RuntimeDiagnostic, ...] = ()

    model_config = {"frozen": True}


class RunEvent(BaseModel):
    schema_version: Literal["qxtrl.rs.RunEvent/v0.1"] = "qxtrl.rs.RunEvent/v0.1"
    event_id: str
    run_id: str
    request_id: str
    parent_run_id: Optional[str] = None
    source_layer: Literal["rs", "cpir", "eb", "ds", "co"]
    stage: Literal[
        "created", "admission", "queued", "validating", "compiling",
        "waiting_for_resources", "resources_acquired", "backend_submit",
        "backend_running", "backend_completed", "analyzing",
        "persisting", "completed", "failed", "cancelled", "cleanup"
    ]
    state: Literal["started", "succeeded", "failed", "skipped", "info"]
    severity: Literal["debug", "info", "warning", "error"] = "info"
    code: str
    message: str
    t_rel_ms: float
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @field_validator("t_rel_ms", mode="before")
    @classmethod
    def _validate_t_rel(cls, v: Any) -> float:
        if isinstance(v, bool):
            raise ValueError("t_rel_ms must be number, not bool")
        if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
            raise ValueError("t_rel_ms must be non-negative finite number")
        return float(v)


class RuntimeDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.rs.RuntimeDiagnostic/v0.1"] = "qxtrl.rs.RuntimeDiagnostic/v0.1"
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    stage: Optional[str] = None
    source_layer: Optional[str] = None
    path: Optional[str] = None
    hint: Optional[str] = None

    model_config = {"frozen": True}


class StageTiming(BaseModel):
    schema_version: Literal["qxtrl.rs.StageTiming/v0.1"] = "qxtrl.rs.StageTiming/v0.1"
    run_id: str
    stage: str
    started_at_ns: int
    ended_at_ns: Optional[int] = None
    duration_ms: Optional[float] = None
    status: Literal["succeeded", "failed", "skipped", "cancelled"]
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @field_validator("duration_ms", mode="before")
    @classmethod
    def _validate_duration(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, bool):
            raise ValueError("duration_ms must be number, not bool")
        if isinstance(v, (int, float)):
            if math.isnan(v) or math.isinf(v):
                raise ValueError("duration_ms must be finite")
            return float(v)
        return v

    @model_validator(mode="after")
    def _validate_timing_consistency(self) -> "StageTiming":
        if self.ended_at_ns is not None and self.started_at_ns > self.ended_at_ns:
            raise ValueError("ended_at_ns must be >= started_at_ns")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        return self


class ResourceLease(BaseModel):
    schema_version: Literal["qxtrl.rs.ResourceLease/v0.1"] = "qxtrl.rs.ResourceLease/v0.1"
    lease_id: str
    run_id: str
    resource_keys: tuple[str, ...]
    acquired: bool
    acquired_at_ns: Optional[int] = None
    expires_at_ns: Optional[int] = None
    release_state: Literal["held", "released", "expired", "failed"] = "held"

    model_config = {"frozen": True}


class RuntimeRunResult(BaseModel):
    schema_version: Literal["qxtrl.rs.RuntimeRunResult/v0.1"] = "qxtrl.rs.RuntimeRunResult/v0.1"
    run_id: str
    request_id: str
    final_state: Literal["succeeded", "failed", "cancelled", "rejected"]
    l1_spec_id: Optional[str] = None
    bundle_id: Optional[str] = None
    backend_id: Optional[str] = None
    backend_result: Optional[BackendRunResult] = None
    analysis_result: Optional[dict[str, Any]] = None
    manifest_ref: Optional[str] = None
    events: tuple[RunEvent, ...] = ()
    diagnostics: tuple[RuntimeDiagnostic, ...] = ()
    timings: tuple[StageTiming, ...] = ()
    metrics: dict[str, float] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_result_consistency(self) -> "RuntimeRunResult":
        if self.final_state == "succeeded":
            has_content = bool(
                self.backend_result is not None or self.manifest_ref or self.analysis_result is not None
            ) or (len(self.events) > 1 and len(self.timings) > 1)
            if not has_content:
                raise ValueError("succeeded result must include backend_result or manifest_ref or analysis (or substantial events/timings)")
        elif self.final_state in ("rejected", "failed"):
            if not any(d.severity == "error" for d in self.diagnostics):
                raise ValueError("rejected/failed result must include at least one error diagnostic")
        elif self.final_state == "cancelled":
            has_cancel = any("CANCEL" in (d.code or "") for d in self.diagnostics) or any("CANCEL" in (e.code or "") for e in self.events)
            if not has_cancel:
                raise ValueError("cancelled result must include a cancel diagnostic or event")
        return self
