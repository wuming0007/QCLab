"""RunManifest and related Pydantic models for L5 ResultStore (SCP-009 aligned)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

# RuntimeRunResult imported inside function to avoid circular import with rs (which imports ds)


class FailureInfo(BaseModel):
    schema_version: Literal["qxtrl.ds.FailureInfo/v0.1"] = "qxtrl.ds.FailureInfo/v0.1"
    code: str
    message: str
    source_layer: Optional[str] = None
    stage: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class TimingMetrics(BaseModel):
    """Aggregated from L4 StageTiming + metrics. Partial allowed with flags."""
    schema_version: Literal["qxtrl.ds.TimingMetrics/v0.1"] = "qxtrl.ds.TimingMetrics/v0.1"
    parse_spec_ms: float = 0.0
    compile_ir_ms: float = 0.0
    submit_backend_ms: float = 0.0
    acquire_result_ms: float = 0.0
    analyze_ms: float = 0.0
    persist_manifest_ms: float = 0.0
    total_duration_ms: float = 0.0
    partial: bool = False  # set by L5 if L4 missed total etc.


class ExperimentManifestRef(BaseModel):
    spec_id: str
    schema_version: str
    spec_hash: Optional[str] = None
    pdca_path: list[dict[str, Any]] = Field(default_factory=list)
    atom_type: Optional[str] = None


class CompileManifestRef(BaseModel):
    bundle_id: Optional[str] = None
    bundle_hash: Optional[str] = None
    pulse_ir_hash: Optional[str] = None


class ExecutionManifestRef(BaseModel):
    backend_id: Optional[str] = None
    mode: str = "virtual"
    backend_final_state: Literal["succeeded", "failed", "cancelled", "rejected", "not_submitted"] = "not_submitted"


class DatasetRef(BaseModel):
    schema_version: Literal["qxtrl.ds.DatasetRef/v0.1"] = "qxtrl.ds.DatasetRef/v0.1"
    dataset_id: str
    run_id: str
    logical_uri: str  # qxtrl://... never absolute FS path
    content_hash: str
    metadata_hash: str
    kind: str = "raw_iq"  # raw_iq, processed, analysis_result, etc.

    model_config = {"frozen": True}

    @field_validator("content_hash", "metadata_hash")
    @classmethod
    def _validate_content_hash(cls, v: str, info: Any) -> str:
        fname = info.field_name
        if not v or v == "sha256:":
            raise ValueError(f"{fname} must not be empty or exactly 'sha256:'")
        if not v.startswith("sha256:"):
            raise ValueError(f"{fname} must start with 'sha256:' prefix (got {v[:20]})")
        hexp = v[7:]
        if len(hexp) not in (16, 64):
            raise ValueError(f"{fname} hex part must be 16 or 64 chars (got len={len(hexp)})")
        if not all(c in "0123456789abcdef" for c in hexp):
            raise ValueError(f"{fname} must contain only lowercase hex after 'sha256:'")
        return v


class DSDiagnostic(BaseModel):
    schema_version: Literal["qxtrl.ds.DSDiagnostic/v0.1"] = "qxtrl.ds.DSDiagnostic/v0.1"
    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    stage: Optional[str] = None
    run_id: Optional[str] = None
    path: Optional[str] = None
    recoverable: bool = False


class RunManifest(BaseModel):
    """Immutable run index / manifest. Produced only by ResultStore.finalize."""
    schema_version: Literal["qxtrl.ds.RunManifest/v0.1"] = "qxtrl.ds.RunManifest/v0.1"
    run_id: str
    final_state: Literal["succeeded", "failed", "cancelled", "rejected"]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    station_id: str = "station.local"
    chip_id: Optional[str] = None
    operator: Optional[str] = None

    experiment: ExperimentManifestRef
    input_snapshots: dict[str, str] = Field(default_factory=dict)
    compile: Optional[CompileManifestRef] = None
    execution: Optional[ExecutionManifestRef] = None

    output_refs: dict[str, list[DatasetRef]] = Field(default_factory=dict)  # raw/processed/...
    events_ref: Optional[DatasetRef] = None
    timings_ref: Optional[DatasetRef] = None
    diagnostics_refs: list[DatasetRef] = Field(default_factory=list)

    timing_metrics: TimingMetrics = Field(default_factory=TimingMetrics)
    failure: Optional[FailureInfo] = None
    partial: bool = False

    model_config = {"frozen": True}

    @model_validator(mode="after")
    def _validate_consistency(self) -> "RunManifest":
        if self.final_state == "succeeded":
            if self.partial:
                raise ValueError("succeeded manifest cannot be partial")
            # For virtual MVP, execution or dry-run evidence expected
            has_exec = (self.execution and self.execution.backend_final_state in ("succeeded",)) or bool(self.output_refs)
            if not has_exec and not self.experiment.spec_id:
                raise ValueError("succeeded manifest should have execution evidence or spec")
        if self.final_state in ("failed", "rejected", "cancelled"):
            if not self.failure and not any("error" in (str(d) or "") for d in (self.diagnostics_refs or [])):
                # allow but prefer failure populated by builder
                pass
        if ".." in self.run_id or "/" in self.run_id or "\\" in self.run_id:
            raise ValueError("run_id must be safe token, no path separators")
        # Enforce output_refs belong to this run (per TRH replay evidence integrity)
        for _g, _refs in (self.output_refs or {}).items():
            for _r in _refs or []:
                r_run = getattr(_r, "run_id", None) or (_r.get("run_id") if isinstance(_r, dict) else None)
                if r_run and r_run != self.run_id:
                    raise ValueError(f"output_ref.run_id={r_run} must equal manifest.run_id={self.run_id}")
                r_uri = getattr(_r, "logical_uri", None) or (_r.get("logical_uri") if isinstance(_r, dict) else None)
                if r_uri and r_uri.startswith("qxtrl://runs/"):
                    uri_rid = r_uri[len("qxtrl://runs/"):].split("/", 1)[0]
                    if uri_rid and uri_rid != self.run_id:
                        raise ValueError(f"output_ref logical_uri run_id={uri_rid} must equal manifest.run_id={self.run_id}")
        return self


# Helper for mapping L4 RuntimeRunResult (used by builder)
def _safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default) if obj is not None else default
