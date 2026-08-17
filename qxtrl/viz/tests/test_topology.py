"""Tests for reusable chip topology maps."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

from qxtrl.viz import ChipLayout, plot_chip_topology, save_topology_figure, willow105_layout
from qxtrl.viz.willow import WILLOW105_DIAGRAM


def test_rectangular_grid_counts():
    layout = ChipLayout.rectangular_grid(2, 3, name="demo")
    assert len(layout.qubits) == 6
    # 2 rows × 2 horizontal bonds + 3 cols × 1 vertical bond = 7
    assert len(layout.couplers) == 7
    assert layout.qubits[0].qubit_id == "q000"
    assert layout.couplers[0].coupler_id.startswith("tc_")


def test_ascii_skips_empty_cells():
    layout = ChipLayout.from_ascii("X-X\n-X-\n", name="plus")
    assert { (q.grid_row, q.grid_col) for q in layout.qubits } == {(0, 0), (0, 2), (1, 1)}
    assert len(layout.couplers) == 0  # no orthogonal neighbours


def test_metric_keywords_are_case_insensitive(tmp_path: Path):
    layout = ChipLayout.rectangular_grid(1, 2)
    layout.set_qubit_metrics("t1", {"q000": 50.0, "q001": 80.0})
    layout.set_coupler_metrics("cz_fidelity", {"tc_q000_q001": 0.995})
    result = plot_chip_topology(layout, qubit_metric="T1", coupler_metric="CZ_FIDELITY")
    assert result.qubit_mappable is not None
    assert result.coupler_mappable is not None
    save_topology_figure(result.fig, tmp_path / "tiny", formats=("png",))
    assert (tmp_path / "tiny.png").is_file()
    plt_close(result)


def test_missing_metrics_still_draw():
    layout = ChipLayout.rectangular_grid(2, 2)
    layout.qubits[0].metrics["t1"] = 70.0
    result = plot_chip_topology(layout, qubit_metric="t1", coupler_metric="cz_fidelity")
    assert result.qubit_mappable is not None
    assert result.coupler_mappable is None
    plt_close(result)


def test_willow105_public_geometry():
    layout = willow105_layout(with_illustrative_metrics=False)
    assert len(layout.qubits) == 105
    # Spec sheet: average connectivity 3.47 (4-way typical).
    degree = layout.average_degree()
    assert 3.40 <= degree <= 3.55
    occupied = WILLOW105_DIAGRAM.count("X")
    assert occupied == 105


def test_willow_illustrative_metrics_are_seeded():
    a = willow105_layout(seed=1)
    b = willow105_layout(seed=1)
    c = willow105_layout(seed=2)
    assert a.qubits[0].metrics["t1"] == pytest.approx(b.qubits[0].metrics["t1"])
    assert a.qubits[0].metrics["t1"] != pytest.approx(c.qubits[0].metrics["t1"])
    assert 0.97 < a.couplers[0].metrics["cz_fidelity"] < 1.0


def test_set_coupler_metrics_by_pair_key():
    layout = ChipLayout.rectangular_grid(1, 2)
    layout.set_coupler_metrics("gate_fidelity", {"q000__q001": 0.99})
    assert layout.couplers[0].metrics["gate_fidelity"] == pytest.approx(0.99)


def test_keyword_switch_changes_mapped_values():
    layout = willow105_layout(seed=0)
    t1 = plot_chip_topology(layout, qubit_metric="t1", coupler_metric="cz_fidelity")
    freq = plot_chip_topology(layout, qubit_metric="frequency", coupler_metric="cz_error")
    t1_arr = np.asarray(t1.qubit_mappable.get_array())
    freq_arr = np.asarray(freq.qubit_mappable.get_array())
    assert t1_arr.mean() > 40.0
    assert 4.5 < freq_arr.mean() < 6.5
    plt_close(t1)
    plt_close(freq)


def test_legend_sits_inside_substrate_and_colorbars_match_height():
    layout = willow105_layout(seed=0)
    result = plot_chip_topology(layout, qubit_metric="t1", coupler_metric="cz_fidelity")
    result.fig.canvas.draw()
    ax = result.ax
    legend = ax.get_legend()
    assert legend is not None
    inv = ax.transData.inverted()
    legend_box = legend.get_window_extent(result.fig.canvas.get_renderer())
    (lx0, ly0), (lx1, ly1) = inv.transform(
        [[legend_box.x0, legend_box.y0], [legend_box.x1, legend_box.y1]]
    )
    spacing = layout.mean_spacing()
    xmin, xmax, ymin, ymax = layout.bounds()
    pad = 0.72 * spacing
    assert lx0 >= xmin - pad - 0.05 * spacing
    assert ly1 <= ymax + pad - 0.25 * spacing
    assert ly0 >= ymin - pad

    sub_h = abs(
        ax.transData.transform((xmin, ymax + pad))[1]
        - ax.transData.transform((xmin, ymin - pad))[1]
    )
    cb_h = result.qubit_cbar.ax.get_window_extent().height
    assert 0.85 * sub_h <= cb_h <= 1.15 * sub_h
    plt_close(result)


def plt_close(result) -> None:
    import matplotlib.pyplot as plt

    plt.close(result.fig)
