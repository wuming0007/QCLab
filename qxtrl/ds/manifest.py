"""Minimal RunManifest for MVP.

Supports both legacy L7-style result dict (for compat) and L3 BackendRunResult.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunManifest:
    run_id: str
    spec_id: str
    l1_schema_version: str
    l0_refs: dict[str, str]
    pdca_path: list[dict]
    result_summary: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


def record_run(
    spec: Any,  # ExperimentSpec
    result: Any,  # dict (legacy) or BackendRunResult (L3)
    analysis: dict,
) -> RunManifest:
    """Record a run for audit (MVP in-memory).

    Accepts:
    - Legacy: result dict from run_rabi_virtual
    - L3: BackendRunResult (preferred path)
    """
    metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}
    proposal = analysis.get("proposal", {}) if isinstance(analysis, dict) else {}

    # Detect L3 BackendRunResult
    if hasattr(result, "final_state") and hasattr(result, "bundle_hash"):
        # L3 path
        backend = getattr(result, "backend_id", "l3_backend")
        points = len(getattr(result, "data", {}).get("iq", [])) if hasattr(result, "data") else 0
        pulse_ir_hash = getattr(result, "pulse_ir_hash", "")
        bundle_id = getattr(result, "bundle_id", "")
        final_state = getattr(result, "final_state", "")
        return RunManifest(
            run_id=f"run_{spec.spec_id}_{hash(str(result)) % 10000}",
            spec_id=spec.spec_id,
            l1_schema_version=spec.schema_version,
            l0_refs={
                "chip": str(spec.l0_context.chip_model_ref),
                "wiring": str(spec.l0_context.wiring_graph_ref),
                "hardware": str(spec.l0_context.hardware_inventory_ref),
                "safety": str(spec.l0_context.safety_policy_ref),
            },
            pdca_path=[p.model_dump() for p in spec.pdca_path],
            result_summary={
                "pi_amp": metrics.get("pi_amp"),
                "contrast": metrics.get("contrast"),
                "fit_quality": metrics.get("fit_quality"),
                "backend": backend,
                "points": points,
                "proposal_value": proposal.get("value"),
                "final_state": final_state,
                "bundle_id": bundle_id,
                "pulse_ir_hash": pulse_ir_hash,
            },
            metadata={
                "source": "l3_eb_mvp_demo",
                "proposal": proposal,
                "backend_result": {
                    "events": [e.model_dump() if hasattr(e, "model_dump") else e for e in getattr(result, "events", [])],
                    "diagnostics": [d.model_dump() if hasattr(d, "model_dump") else d for d in getattr(result, "diagnostics", [])],
                },
            },
        )
    else:
        # Legacy path (direct L7 result dict)
        return RunManifest(
            run_id=f"run_{spec.spec_id}_{hash(str(result)) % 10000}",
            spec_id=spec.spec_id,
            l1_schema_version=spec.schema_version,
            l0_refs={
                "chip": str(spec.l0_context.chip_model_ref),
                "wiring": str(spec.l0_context.wiring_graph_ref),
                "hardware": str(spec.l0_context.hardware_inventory_ref),
                "safety": str(spec.l0_context.safety_policy_ref),
            },
            pdca_path=[p.model_dump() for p in spec.pdca_path],
            result_summary={
                "pi_amp": metrics.get("pi_amp"),
                "contrast": metrics.get("contrast"),
                "fit_quality": metrics.get("fit_quality"),
                "backend": result.get("backend"),
                "points": result.get("scan_points"),
                "proposal_value": proposal.get("value"),
            },
            metadata={
                "source": "l1_mvp_demo",
                "proposal": proposal,
            },
        )
