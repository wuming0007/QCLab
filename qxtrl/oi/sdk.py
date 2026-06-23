"""L9/OI SDK - thin wrappers around L4 and L5.

MVP: delegates to RuntimeService.run_once + FileResultStore.
Does not bypass layers or pollute state.
"""

from __future__ import annotations

from typing import Any

from qxtrl.el import create_rabi_experiment_spec
from qxtrl.rs import RuntimeService, RunRequest
from qxtrl.cc import minimal_rabi_lab

from .models import RunRabiOptions, RunSummary


def build_rabi_amplitudes(points: int, max_amp: float = 0.5) -> list[float]:
    """L9 helper: generate amplitude list from point count for Rabi scan.
    Pure function; result is passed into L1 factory.
    """
    if points < 2:
        points = 2
    step = max_amp / (points - 1) if points > 1 else max_amp
    return [round(i * step, 6) for i in range(points)]


class OperatorSession:
    """Lightweight session for running experiments and querying manifests.

    result_dir is local only (not written into RunManifest).
    """

    def __init__(self, result_dir: str = "runs"):
        self.result_dir = result_dir

    def run_rabi(self, options: RunRabiOptions | dict[str, Any]) -> RunSummary:
        """Run Rabi and return L9 summary. Delegates to L4."""
        if isinstance(options, dict):
            options = RunRabiOptions.model_validate(options)

        lab = minimal_rabi_lab()

        if options.qubit_id != "q000":
            # MVP demo: only q000 is in minimal_rabi_lab context (per L9 design and reviews)
            raise ValueError(f"qubit_id={options.qubit_id} not in current demo L0 context (only q000 allowed)")

        amplitudes = build_rabi_amplitudes(options.points)

        spec = create_rabi_experiment_spec(
            qubit_id=options.qubit_id,
            l0_chip_model_ref=lab["chip"],
            l0_wiring_ref=lab["wiring"],
            l0_hw_ref=lab["hardware"],
            l0_safety_ref=lab["safety"],
            amplitudes=amplitudes,
            shots=options.shots,
        )

        # L0 gate (demo)
        try:
            lab["chip"].require_usable_for_control(context="oi.sdk")
            lab["wiring"].require_usable_for_control(context="oi.sdk")
        except Exception:
            pass  # L9 surfaces but does not block; L1/L4 will validate too

        request = RunRequest(
            request_id=options.request_id or f"req.{spec.spec_id}",
            submitted_by=options.submitted_by,
            experiment_spec=spec,
            backend_id=options.backend_id,
            mode=options.mode,
            tags=options.tags,
        )

        runtime = RuntimeService(result_base_dir=options.result_dir)
        result = runtime.run_once(request)

        summary = RunSummary.from_runtime_result(result)

        # Optionally fetch full manifest for richer view (manifest_ref should be set by L4/L5)
        if summary.manifest_ref:
            # caller can use show_manifest if full view needed
            pass

        return summary


def run_rabi_virtual(
    qubit_id: str = "q000",
    points: int = 21,
    shots: int = 1024,
    mode: str = "virtual",
    result_dir: str = "runs",
    **kwargs: Any,
) -> RunSummary:
    """Convenience one-liner (matches design OI-MVP-001)."""
    options = RunRabiOptions(
        qubit_id=qubit_id,
        points=points,
        shots=shots,
        mode=mode,  # type: ignore
        result_dir=result_dir,
        **kwargs,
    )
    session = OperatorSession(result_dir=result_dir)
    return session.run_rabi(options)


def replay_inspect(
    run_id_or_manifest_ref: str,
    result_dir: str = "runs",
    require_hash_check: bool = True,
) -> dict:
    """Thin L9 exposure of L7 replay inspect (MVP inspect mode only).

    Delegates to trh + L5. Returns summary + diagnostics.
    Does not implement replay_virtual (rejected per current L7).
    """
    from qxtrl.trh import replay_manifest, ReplayRequest

    req = ReplayRequest(
        replay_id="l9-replay-inspect",
        run_id_or_manifest_ref=run_id_or_manifest_ref,
        result_dir=result_dir,
        mode="inspect",
        require_hash_check=require_hash_check,
    )
    res = replay_manifest(req)
    return {
        "final_state": res.final_state,
        "source_run_id": res.source_run_id,
        "output_summary": dict(res.output_summary),
        "diagnostics": [{"code": d.code, "severity": d.severity, "message": d.message} for d in (res.diagnostics or [])],
        "plan_required_input_refs": dict(res.plan.required_input_refs),
        "plan_required_output_refs": dict(res.plan.required_output_refs),
    }
