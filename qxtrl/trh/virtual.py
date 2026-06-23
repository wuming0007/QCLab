"""L7/TRH Virtual Rabi implementation (MVP).

Uses typed models, deterministic seeded RNG (random.Random), PulseIR priority.
Legacy dict/ExperimentSpec fallback for transition.
"""

import math
import random
from typing import Any

from qxtrl.cpir.pulse_ir import PulseIR
from qxtrl.el.models import ExperimentSpec

from .models import (
    TwinModelRef,
    VirtualRunRequest,
    VirtualRunResult,
)


DEFAULT_MODEL_REF = TwinModelRef(
    model_id="trh.model.rabi_mvp",
    model_version="v0.1",
    model_kind="rabi_virtual_mvp",
    source="built_in",
)


def _extract_sweep_values(compiled: PulseIR | ExperimentSpec | dict, default_key: str = "amp") -> tuple[str, list[float]]:
    """Extract scan values and the parameter key (amp or dur).
    Returns (axis_key, values).
    """
    values = [0.0, 0.05, 0.10, 0.15, 0.20]
    key = default_key

    # New structured path
    sweep_obj = getattr(compiled, "sweep", None) or (compiled.get("sweep") if isinstance(compiled, dict) else None)
    if sweep_obj and getattr(sweep_obj, "axes", None):
        ax = sweep_obj.axes[0]
        values = list(ax.values)
        key = "dur" if "duration" in getattr(ax, "parameter_ref", "") else "amp"
        return key, values
    if isinstance(compiled, dict) and "sweep" in compiled:
        sw = compiled["sweep"]
        if isinstance(sw, dict) and sw.get("axes"):
            ax = sw["axes"][0]
            values = list(ax.get("values", values))
            key = "dur" if "duration" in ax.get("parameter_ref", "") else "amp"
            return key, values

    # Fallback from plan
    if hasattr(compiled, "plan") and hasattr(compiled.plan, "scan") and compiled.plan.scan.axes:
        ax = compiled.plan.scan.axes[0]
        values = list(ax.values)
        key = "dur" if "duration" in getattr(ax, "parameter_ref", "") else "amp"
        return key, values

    return key, values


def _run_rabi_deterministic(
    sweep_values: list[float],
    fixed_or_hidden: float,
    noise_sigma: float,
    seed: int,
    x_label: str = "amp",
) -> list[dict[str, float]]:
    """Core deterministic Rabi simulation.
    For amplitude scan: fixed_or_hidden = hidden_pi_amp
    For duration scan at fixed amp: fixed_or_hidden = the fixed amplitude (Omega ~ amp)
    """
    rng = random.Random(seed)
    iq_data = []
    for val in sweep_values:
        if x_label == "dur":
            # Time Rabi at fixed amplitude: oscillation vs duration
            amp = fixed_or_hidden
            if amp > 0:
                p = (math.sin(math.pi / 2 * val * amp / 0.175)) ** 2   # simple scaling
            else:
                p = 0.0
            entry = {"duration_ns": round(val, 1), "amp": round(val, 1),  # compat for current analyzer
                     "i": round((1.0 - 2.0 * p) + rng.gauss(0, noise_sigma), 6),
                     "q": round(rng.gauss(0, noise_sigma * 0.08), 6)}
        else:
            amp = val
            if fixed_or_hidden > 0:
                p = (math.sin(math.pi / 2 * amp / fixed_or_hidden)) ** 2
            else:
                p = 0.0
            entry = {"amp": round(amp, 4), "i": round((1.0 - 2.0 * p) + rng.gauss(0, noise_sigma), 6),
                     "q": round(rng.gauss(0, noise_sigma * 0.08), 6)}
        iq_data.append(entry)
    return iq_data


def run_rabi_virtual(
    compiled: PulseIR | ExperimentSpec | dict,
    noise: float = 0.015,
    seed: int = 42,
) -> dict[str, Any]:
    """Legacy-compatible entry. Prefer typed run_rabi_virtual_typed for new code.

    Returns dict for backward compat with L3.
    Hardened with basic numeric guards matching VirtualQPUConfig (prevents easy NaN/Inf bypass).
    """
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be int, not bool or other")
    if isinstance(noise, bool) or not isinstance(noise, (int, float)) or math.isnan(noise) or math.isinf(noise) or noise < 0:
        raise ValueError("noise must be finite non-negative number")
    amps = _extract_amps(compiled)
    hidden_pi_amp = 0.175
    iq = _run_rabi_deterministic(amps, hidden_pi_amp, noise, seed)
    return {
        "result": iq,
        "shots": 1024,
        "backend": "virtual_mvp",
        "noise": noise,
        "scan_points": len(amps),
        "_hidden_pi_amp": hidden_pi_amp,
    }


def run_rabi_virtual_typed(request: VirtualRunRequest) -> VirtualRunResult:
    """Typed L7 entry per design. L3-facing preferred."""
    pulse_ir = request.pulse_ir
    config = request.config

    key, values = _extract_sweep_values(pulse_ir)
    model_ref = config.model_ref
    hidden = config.hidden_parameters or {}
    hidden_pi_amp = hidden.get("pi_amp", 0.175)

    # For duration scan we pass the fixed amp from Do.parameters if present (simplified)
    fixed = 0.1
    iq = _run_rabi_deterministic(values, hidden_pi_amp if key == "amp" else fixed,
                                  config.noise_sigma, config.seed, x_label=key)

    data = {"iq": iq, "scan_points": len(values)}
    if key == "dur":
        data["x_axis"] = "duration_ns"
    else:
        data["x_axis"] = "amp"

    return VirtualRunResult(
        run_id=request.run_id,
        final_state="succeeded",
        model_ref=model_ref,
        seed=config.seed,
        result_level=request.result_level,
        data=data,
        diagnostics=(),
        metrics={"points": len(values)},
    )
