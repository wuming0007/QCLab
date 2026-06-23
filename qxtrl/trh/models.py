"""L7/TRH Pydantic models per QXtrl_L7_TRH_TwinReplayHIL_设计.md."""

from __future__ import annotations

import math
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# Cross layer
from qxtrl.cpir.pulse_ir import PulseIR


class TRHDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.trh.TRHDiagnostic/v0.1"] = "qxtrl.trh.TRHDiagnostic/v0.1"
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    stage: Optional[str] = None
    path: Optional[str] = None
    hint: Optional[str] = None


class TwinModelRef(BaseModel):
    schema_version: Literal["qxtrl.trh.TwinModelRef/v0.1"] = "qxtrl.trh.TwinModelRef/v0.1"
    model_id: str
    model_version: str
    model_kind: Literal["rabi_virtual_mvp", "instrument_virtual", "replay", "hil"]
    content_hash: Optional[str] = None
    source: Literal["built_in", "config_snapshot", "fit_result", "external"] = "built_in"


class VirtualQPUConfig(BaseModel):
    schema_version: Literal["qxtrl.trh.VirtualQPUConfig/v0.1"] = "qxtrl.trh.VirtualQPUConfig/v0.1"
    model_ref: TwinModelRef
    seed: int = 42
    noise_sigma: float = 0.015
    hidden_parameters: dict[str, float] = Field(default_factory=dict)
    fault_injection: dict[str, Any] = Field(default_factory=dict)

    # MVP defaults
    # hidden: pi_amp etc.

    @field_validator("seed", mode="before")
    @classmethod
    def _validate_seed(cls, v: Any) -> int:
        if isinstance(v, bool):
            raise ValueError("seed must be int, not bool")
        if not isinstance(v, int):
            raise ValueError("seed must be integer")
        return v

    @field_validator("noise_sigma", mode="before")
    @classmethod
    def _validate_noise(cls, v: Any) -> float:
        if isinstance(v, bool):
            raise ValueError("noise_sigma must not be bool")
        if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
            raise ValueError("noise_sigma must be finite non-negative number")
        return float(v)

    @model_validator(mode="after")
    def _validate_hidden_and_fault(self) -> "VirtualQPUConfig":
        for k, val in self.hidden_parameters.items():
            if not isinstance(k, str) or not k:
                raise ValueError("hidden_parameters keys must be non-empty strings")
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                raise ValueError(f"hidden_parameters[{k}] must be finite number")
            if k == "pi_amp" and val <= 0:
                raise ValueError("hidden pi_amp must be > 0")
        # fault_injection strict JSON-like, no NaN etc.
        def _is_strict_json(o: Any) -> bool:
            if o is None or isinstance(o, (bool, int, str)):
                return True
            if isinstance(o, float):
                return not (math.isnan(o) or math.isinf(o))
            if isinstance(o, list):
                return all(_is_strict_json(x) for x in o)
            if isinstance(o, dict):
                return all(isinstance(kk, str) and _is_strict_json(vv) for kk, vv in o.items())
            return False
        if not _is_strict_json(self.fault_injection):
            raise ValueError("fault_injection must be strict JSON-like (no NaN/Inf, objects, sets)")
        return self


class VirtualRunRequest(BaseModel):
    schema_version: Literal["qxtrl.trh.VirtualRunRequest/v0.1"] = "qxtrl.trh.VirtualRunRequest/v0.1"
    request_id: str
    run_id: str
    pulse_ir: PulseIR
    config: VirtualQPUConfig
    result_level: Literal["integrated_iq"] = "integrated_iq"


class VirtualRunResult(BaseModel):
    schema_version: Literal["qxtrl.trh.VirtualRunResult/v0.1"] = "qxtrl.trh.VirtualRunResult/v0.1"
    run_id: str
    final_state: Literal["succeeded", "failed", "rejected"]
    model_ref: TwinModelRef
    seed: int
    result_level: str
    data: dict[str, Any] = Field(default_factory=dict)
    diagnostics: tuple[TRHDiagnostic, ...] = ()
    metrics: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_data_finite(self) -> "VirtualRunResult":
        def _has_nan_inf(o: Any) -> bool:
            if isinstance(o, float):
                return math.isnan(o) or math.isinf(o)
            if isinstance(o, list):
                return any(_has_nan_inf(x) for x in o)
            if isinstance(o, dict):
                return any(_has_nan_inf(v) for v in o.values())
            return False
        if _has_nan_inf(self.data):
            raise ValueError("VirtualRunResult.data must not contain NaN or Inf")
        return self


class ReplayRequest(BaseModel):
    schema_version: Literal["qxtrl.trh.ReplayRequest/v0.1"] = "qxtrl.trh.ReplayRequest/v0.1"
    replay_id: str
    run_id_or_manifest_ref: str
    result_dir: str = "runs"
    mode: Literal["inspect", "replay_virtual", "replay_recorded", "compare"] = "inspect"
    require_hash_check: bool = True


class ReplayPlan(BaseModel):
    schema_version: Literal["qxtrl.trh.ReplayPlan/v0.1"] = "qxtrl.trh.ReplayPlan/v0.1"
    replay_id: str
    source_run_id: str
    source_manifest_ref: str
    mode: str
    required_input_refs: dict[str, str] = Field(default_factory=dict)
    required_output_refs: dict[str, list[str]] = Field(default_factory=dict)
    expected_hashes: dict[str, str] = Field(default_factory=dict)
    diagnostics: tuple[TRHDiagnostic, ...] = ()


class ReplayResult(BaseModel):
    schema_version: Literal["qxtrl.trh.ReplayResult/v0.1"] = "qxtrl.trh.ReplayResult/v0.1"
    replay_id: str
    source_run_id: str
    final_state: Literal["succeeded", "failed", "rejected"]
    mode: str
    plan: ReplayPlan
    output_summary: dict[str, Any] = Field(default_factory=dict)
    diagnostics: tuple[TRHDiagnostic, ...] = ()
