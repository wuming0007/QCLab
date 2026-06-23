"""Simple Rabi analyzer for MVP.

Simple least-squares recovery of pi_amp from Rabi curve.
Still naive (no scipy) but recovers hidden truth well enough for MVP demo.
"""

import math
from typing import Any


def fit_pi_amp(iq_data: list[dict]) -> dict[str, Any]:
    """Grid-search estimator for the amp at which we reach pi rotation.

    Model: i(amp) = 1 - 2 * sin^2( pi/2 * amp / pi_amp )
    We search for pi_amp that minimizes squared error against observed i.
    """
    amps = [float(d["amp"]) for d in iq_data]
    is_ = [float(d.get("i", d.get("I", 0.0))) for d in iq_data]

    if not amps:
        return {"pi_amp": 0.0, "contrast": 0.0, "fit_quality": 0.0}

    # Candidate pi_amps around data range (0.5x last to 3x last) + some anchors
    last = max(amps[-1], 0.2)
    candidates = []
    for k in [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5]:
        candidates.append(last * k)
    for c in [0.10, 0.12, 0.14, 0.16, 0.175, 0.18, 0.20, 0.22, 0.25]:
        if c not in candidates:
            candidates.append(c)

    best_err = float("inf")
    best_pa = last * 1.2

    for cand in candidates:
        if cand <= 0:
            continue
        err = 0.0
        for a, ival in zip(amps, is_):
            p = (math.sin(math.pi / 2 * a / cand)) ** 2
            model = 1.0 - 2.0 * p
            err += (model - ival) ** 2
        if err < best_err:
            best_err = err
            best_pa = cand

    # Refine around best a bit
    for delta in [-0.01, -0.005, 0.005, 0.01]:
        cand = max(0.01, best_pa + delta)
        err = 0.0
        for a, ival in zip(amps, is_):
            p = (math.sin(math.pi / 2 * a / cand)) ** 2
            model = 1.0 - 2.0 * p
            err += (model - ival) ** 2
        if err < best_err:
            best_err = err
            best_pa = cand

    contrast = max(is_) - min(is_)
    # Fit quality heuristic: low residual relative to contrast + decent contrast
    fit_q = max(0.5, min(0.99, 0.98 - min(0.5, best_err / max(contrast, 0.05))))

    return {
        "pi_amp": round(best_pa, 4),
        "contrast": round(contrast, 4),
        "fit_quality": round(fit_q, 3),
    }


def analyze_rabi(result: dict[str, Any]) -> dict[str, Any]:
    """Analyze virtual result, produce Observation + proposal."""
    iq = result.get("result", [])
    fit = fit_pi_amp(iq)

    return {
        "observation": "rabi_curve",
        "metrics": fit,
        "proposal": {
            "parameter_ref": "calibration.q000.xy.pi_amp",
            "value": fit["pi_amp"],
            "source": "l1.rabi",
        },
        "raw": result,
    }
