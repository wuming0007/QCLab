"""L9/OI Pydantic models (user-facing).

Aligned with design §5. Thin view models on top of L4/L5.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator
import math


class RunRabiOptions(BaseModel):
    schema_version: Literal["qxtrl.oi.RunRabiOptions/v0.1"] = "qxtrl.oi.RunRabiOptions/v0.1"
    qubit_id: str
    points: int = 21
    shots: int = 1024
    mode: Literal["virtual", "dry_run"] = "virtual"
    backend_id: str = "backend.virtual.rabi_mvp"
    result_dir: str = "runs"
    request_id: Optional[str] = None
    submitted_by: Optional[str] = None
    output_format: Literal["object", "text", "json"] = "object"
    tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("points")
    @classmethod
    def _validate_points(cls, v: int) -> int:
        if isinstance(v, bool) or not isinstance(v, int) or v < 2:
            raise ValueError("points must be integer >= 2")
        return v

    @field_validator("shots")
    @classmethod
    def _validate_shots(cls, v: int) -> int:
        if isinstance(v, bool) or not isinstance(v, int) or v < 1:
            raise ValueError("shots must be integer >= 1")
        return v

    @field_validator("tags")
    @classmethod
    def _validate_tags(cls, v: dict) -> dict:
        def _is_json_like(o: Any) -> bool:
            if o is None or isinstance(o, (bool, int, float, str)):
                if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
                    return False
                return True
            if isinstance(o, list):
                return all(_is_json_like(x) for x in o)
            if isinstance(o, dict):
                return all(isinstance(k, (str, int)) and _is_json_like(val) for k, val in o.items())
            return False

        if not _is_json_like(v):
            raise ValueError("tags must be strict JSON-like (no objects, sets, NaN)")
        return v


class OperatorDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.oi.OperatorDiagnostic/v0.1"] = "qxtrl.oi.OperatorDiagnostic/v0.1"
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    source_layer: Optional[str] = None
    stage: Optional[str] = None
    path: Optional[str] = None
    hint: Optional[str] = None


class RunSummary(BaseModel):
    schema_version: Literal["qxtrl.oi.RunSummary/v0.1"] = "qxtrl.oi.RunSummary/v0.1"
    run_id: str
    request_id: str
    final_state: Literal["succeeded", "failed", "cancelled", "rejected"]
    backend_id: Optional[str] = None
    bundle_id: Optional[str] = None
    manifest_ref: Optional[str] = None
    total_duration_ms: Optional[float] = None
    analysis_summary: dict[str, Any] = Field(default_factory=dict)
    diagnostics: tuple[OperatorDiagnostic, ...] = ()
    event_count: int = 0

    @classmethod
    def from_runtime_result(cls, result: Any) -> "RunSummary":
        """Convert L4 RuntimeRunResult to L9 view. Preserves diagnostics."""
        diags = []
        for d in getattr(result, "diagnostics", ()) or ():
            diags.append(OperatorDiagnostic(
                severity=d.severity,
                code=d.code,
                message=d.message,
                source_layer=getattr(d, "source_layer", None),
                stage=getattr(d, "stage", None),
                path=getattr(d, "path", None),
                hint=getattr(d, "hint", None),
            ))

        analysis = {}
        if getattr(result, "analysis_result", None):
            analysis = result.analysis_result if isinstance(result.analysis_result, dict) else {"raw": str(result.analysis_result)[:200]}

        return cls(
            run_id=result.run_id,
            request_id=result.request_id,
            final_state=result.final_state,
            backend_id=getattr(result, "backend_id", None),
            bundle_id=getattr(result, "bundle_id", None),
            manifest_ref=getattr(result, "manifest_ref", None),
            total_duration_ms=result.metrics.get("total_duration_ms") if hasattr(result, "metrics") else None,
            analysis_summary=analysis,
            diagnostics=tuple(diags),
            event_count=len(getattr(result, "events", ()) or ()),
        )


class ManifestView(BaseModel):
    schema_version: Literal["qxtrl.oi.ManifestView/v0.1"] = "qxtrl.oi.ManifestView/v0.1"
    run_id: str
    final_state: str
    manifest_ref: str
    input_refs: dict[str, Any] = Field(default_factory=dict)
    output_refs: dict[str, Any] = Field(default_factory=dict)
    timings: dict[str, float] = Field(default_factory=dict)
    diagnostics: tuple[OperatorDiagnostic, ...] = ()
