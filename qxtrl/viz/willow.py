"""Public Google Willow (105-qubit) layout for topology maps.

The occupancy grid matches Cirq's published ``willow_pink`` / Willow105
device specification (nearest-neighbour square lattice on a truncated
diamond). Per-qubit and per-coupler numbers are **not** Google's
measured device map: they are reproducible illustrative samples drawn
from the published Chip-1 QEC aggregate statistics on the Willow spec
sheet (9 Dec 2024):

- T1 = 68 ± 13 µs
- simultaneous CZ error = 0.33% ± 0.18%

Do not use these samples for control, calibration, or performance claims.
"""

from __future__ import annotations

import numpy as np

from .topology import ChipLayout

# Cirq GridQubit(row, col) occupancy for willow_pink_d7v1 (105 sites).
# '-' empty, 'X' qubit. Row 0 is the top of the figure (y decreasing down).
WILLOW105_DIAGRAM = """
------XXX------
-----XXXX------
----XXXXXXX----
---XXXXXXXX----
--XXXXXXXXXXX--
-XXXXXXXXXXXX--
XXXXXXXXXXXXXXX
--XXXXXXXXXXXX-
--XXXXXXXXXXX--
----XXXXXXXX---
----XXXXXXX----
------XXXX-----
------XXX------
"""

WILLOW_NOTES = (
    "Layout: public Cirq willow_pink / Willow105 occupancy (nearest-neighbour "
    "square lattice). Colours are illustrative samples from published Chip-1 "
    "QEC aggregates (T1 = 68±13 µs, CZ error = 0.33%±0.18%), not a measured map."
)

WILLOW_CAPTION = (
    "Two-dimensional topology of the public Willow105 occupancy. Circles are "
    "physical qubits coloured by the selected single-qubit metric; squares are "
    "nearest-neighbour couplers coloured by the selected two-qubit metric. "
    "The grid follows Cirq's published willow_pink device specification "
    "(105 qubits, mean degree 3.47). Colours in the example figure are "
    "illustrative samples drawn from the Willow Chip-1 QEC aggregates "
    r"($T_1 = 68\pm13~\mu\mathrm{s}$, CZ error $=0.33\%\pm0.18\%$), "
    "not a measured per-device map."
)

# Spec-sheet Chip 1 (QEC) aggregates, used only to scale illustrative samples.
_T1_MEAN_US = 68.0
_T1_STD_US = 13.0
_CZ_ERR_MEAN = 0.0033
_CZ_ERR_STD = 0.0018


def willow105_layout(
    *,
    seed: int = 0,
    with_illustrative_metrics: bool = True,
) -> ChipLayout:
    """Return the public 105-qubit Willow layout.

    Parameters
    ----------
    seed
        RNG seed for illustrative metrics (ignored if metrics are disabled).
    with_illustrative_metrics
        If True, attach synthetic ``t1``, ``t2``, ``frequency``,
        ``cz_fidelity``, and ``cz_error`` fields. If False, the graph
        is geometry-only so callers can inject lab data via
        :meth:`ChipLayout.set_qubit_metrics` / ``set_coupler_metrics``.
    """
    layout = ChipLayout.from_ascii(
        WILLOW105_DIAGRAM,
        name="Willow105",
        notes=WILLOW_NOTES,
    )
    if with_illustrative_metrics:
        _attach_illustrative_metrics(layout, seed=seed)
    return layout


def _attach_illustrative_metrics(layout: ChipLayout, *, seed: int) -> None:
    rng = np.random.default_rng(seed)
    xs = np.array([q.x for q in layout.qubits], dtype=float)
    ys = np.array([q.y for q in layout.qubits], dtype=float)
    x_span = float(xs.max() - xs.min())
    y_span = float(ys.max() - ys.min())
    x_n = np.zeros_like(xs) if x_span == 0 else (xs - xs.mean()) / x_span
    y_n = np.zeros_like(ys) if y_span == 0 else (ys - ys.mean()) / y_span
    spatial = 0.35 * np.sin(2.2 * x_n) + 0.25 * np.cos(1.8 * y_n)

    t1 = _T1_MEAN_US + _T1_STD_US * (0.72 * rng.normal(size=len(layout.qubits)) + 0.55 * spatial)
    t1 = np.clip(t1, 38.0, 115.0)
    t2 = np.clip(0.62 * t1 * (1.0 + 0.12 * rng.normal(size=t1.shape)), 20.0, 2.0 * t1)
    freq = 5.35 + 0.55 * x_n + 0.12 * rng.normal(size=t1.shape)
    freq = np.clip(freq, 4.70, 6.20)

    for q, t1_i, t2_i, f_i in zip(layout.qubits, t1, t2, freq):
        q.metrics["t1"] = float(t1_i)
        q.metrics["t2"] = float(t2_i)
        q.metrics["frequency"] = float(f_i)

    for c in layout.couplers:
        err = float(np.clip(rng.normal(_CZ_ERR_MEAN, _CZ_ERR_STD), 0.0006, 0.012))
        c.metrics["cz_error"] = err
        c.metrics["cz_fidelity"] = 1.0 - err
        c.metrics["gate_fidelity"] = 1.0 - err
