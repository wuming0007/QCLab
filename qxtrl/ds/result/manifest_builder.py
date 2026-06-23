from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional

from ..contracts.manifest import (  # noqa: E402
    RunManifest,
    ExperimentManifestRef,
    CompileManifestRef,
    ExecutionManifestRef,
    FailureInfo,
    TimingMetrics,
    DatasetRef,
)
from ..contracts.errors import DSCode, DSError  # noqa: E402


def _compute_hash(data: Any) -> str:
    """Simple content hash for MVP (json canonical)."""
    if isinstance(data, (dict, list)):
        s = json.dumps(data, sort_keys=True, default=str)
    else:
        s = str(data)
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def _map_timing_metrics(timings: list, total_ms: Optional[float]) -> TimingMetrics:
    tm = {}
    for t in timings or []:
        stage = getattr(t, "stage", "")
        dur = getattr(t, "duration_ms", 0) or 0
        if "parse" in stage or "validate" in stage:
            tm["parse_spec_ms"] = tm.get("parse_spec_ms", 0) + dur
        elif "compile" in stage:
            tm["compile_ir_ms"] = tm.get("compile_ir_ms", 0) + dur
        elif "submit" in stage or "backend" in stage:
            tm["submit_backend_ms"] = tm.get("submit_backend_ms", 0) + dur
        elif "analyze" in stage:
            tm["analyze_ms"] = tm.get("analyze_ms", 0) + dur
        elif "persist" in stage:
            tm["persist_manifest_ms"] = tm.get("persist_manifest_ms", 0) + dur
    if total_ms is not None:
        tm["total_duration_ms"] = total_ms
    partial = "total" not in [getattr(t, "stage", "") for t in (timings or [])]
    return TimingMetrics(**{k: float(v) for k, v in tm.items()}, partial=partial)


def build_from_runtime_result(
    runtime_result: Any,
    spec: Any = None,
    bundle: Any = None,
) -> RunManifest:
    """Primary builder. Consumes L4 output. Produces immutable manifest draft (finalize later)."""
    if not runtime_result or not runtime_result.run_id:
        raise DSError(DSCode.MANIFEST_INCOMPLETE, "runtime_result missing run_id")

    run_id = runtime_result.run_id
    final_state = runtime_result.final_state

    # Experiment ref
    spec_id = runtime_result.l1_spec_id or (getattr(spec, "spec_id", run_id) if spec else run_id)
    exp_ref = ExperimentManifestRef(
        spec_id=spec_id,
        schema_version=getattr(spec, "schema_version", "qxtrl.el.ExperimentSpec/v0.1") if spec else "unknown",
        spec_hash=_compute_hash(spec.model_dump()) if spec else None,
        pdca_path=[p.model_dump() if hasattr(p, "model_dump") else p for p in (getattr(spec, "pdca_path", []) or [])],
        atom_type=getattr(getattr(spec, "check", None), "atom_type", None) or "rabi",
    )

    # input_snapshots from L0 context if available - always stable ref (not full object repr)
    def _stable_ref(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, str):
            return v
        # L0SnapshotRef or similar
        if hasattr(v, "snapshot_id"):
            return str(v.snapshot_id)
        if hasattr(v, "identity") and hasattr(v.identity, "id"):
            return str(v.identity.id)
        if hasattr(v, "id"):
            return str(v.id)
        if hasattr(v, "spec_id"):
            return str(v.spec_id)
        # last resort - truncated to avoid huge reprs
        s = str(v)
        return s[:60] + "..." if len(s) > 60 else s

    input_snaps = {}
    if spec and hasattr(spec, "l0_context"):
        ctx = spec.l0_context
        for k in ("chip_model_ref", "wiring_graph_ref", "hardware_inventory_ref", "safety_policy_ref"):
            v = getattr(ctx, k, None)
            if v:
                input_snaps[k.replace("_ref", "")] = _stable_ref(v)
    elif spec:
        # fallback
        raw = getattr(spec, "l0_refs", {}) or {}
        input_snaps = {kk: _stable_ref(vv) for kk, vv in raw.items()}

    # Compile (prefer bundle param if provided per review)
    br = runtime_result.backend_result
    compile_ref = None
    bndl = bundle or br
    if runtime_result.bundle_id or (bndl and getattr(bndl, "bundle_id", None)):
        compile_ref = CompileManifestRef(
            bundle_id=runtime_result.bundle_id or getattr(bndl, "bundle_id", None),
            bundle_hash=getattr(bndl, "bundle_hash", None) if bndl else (getattr(br, "bundle_hash", None) if br else None),
            pulse_ir_hash = getattr(getattr(bndl, 'pulse_ir', None), 'content_hash', None) if bndl and hasattr(bndl, 'pulse_ir') else getattr(bndl, "pulse_ir_hash", None) if bndl else (getattr(br, "pulse_ir_hash", None) if br else None),
        )

    # Execution
    exec_ref = ExecutionManifestRef(
        backend_id=runtime_result.backend_id,
        mode=getattr(br, "mode", "virtual") if br else "virtual",
        backend_final_state=getattr(br, "final_state", "not_submitted") if br else "not_submitted",
    )

    # Timing
    total = runtime_result.metrics.get("total_duration_ms")
    timing_m = _map_timing_metrics(list(runtime_result.timings or []), total)

    # Failure / partial
    failure = None
    partial = timing_m.partial
    diags = list(runtime_result.diagnostics or [])
    if final_state in ("failed", "rejected", "cancelled") and diags:
        first_err = next((d for d in diags if d.severity == "error"), diags[0])
        failure = FailureInfo(
            code=first_err.code,
            message=first_err.message,
            source_layer=first_err.source_layer,
            stage=first_err.stage,
        )
        if "TIMING" in first_err.code:
            partial = True
            # record DS diagnostic in spirit
            # (store will handle writing)

    # Build minimal output refs (real write_dataset will populate real refs)
    output_refs: dict[str, list[DatasetRef]] = {}
    if br and getattr(br, "data", None):
        pass  # populated by store

    # If analysis present, store will write it as dataset (caller in file_store handles)
    # Events / timings / diags as potential (populated by store)
    events_ref = None
    timings_ref = None
    diag_refs: list[DatasetRef] = []

    # Times: always set completed for terminal runs
    now = datetime.now(timezone.utc)
    started = getattr(runtime_result, "started_at", None) or None  # may not exist
    completed = now

    manifest = RunManifest(
        run_id=run_id,
        final_state=final_state,
        experiment=exp_ref,
        input_snapshots=input_snaps,
        compile=compile_ref,
        execution=exec_ref,
        output_refs=output_refs,
        events_ref=events_ref,
        timings_ref=timings_ref,
        diagnostics_refs=diag_refs,
        timing_metrics=timing_m,
        failure=failure,
        partial=partial,
        started_at=started,
        completed_at=completed,
    )
    # If no backend entered (early reject), execution.backend_final_state = not_submitted already
    return manifest
