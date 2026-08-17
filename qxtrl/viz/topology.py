"""Reusable 2-D quantum-chip topology maps.

Qubits are drawn as circles; couplers as squares at bond midpoints.
Fill color is bound to a named metric (keyword) on each site, so the
same layout can be recoloured for T1, T2, frequency, two-qubit
fidelity, and so on.

The layout model is hardware-agnostic: any chip that can be expressed
as planar sites plus two-qubit edges can be plotted. Google Willow is
one instance; rectangular grids and ASCII diagrams are also supported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from matplotlib.axes import Axes
from matplotlib.cm import ScalarMappable
from matplotlib.collections import PatchCollection
from matplotlib.colorbar import Colorbar
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter

from .style import FigurePreset, apply_publication_style, figure_size_inch

EMPTY_DIAGRAM_CHARS = frozenset("-. \t")

# Keyword → colorbar math text. Unknown keys fall back to the raw keyword.
METRIC_LABELS: dict[str, str] = {
    "t1": r"$T_1$ ($\mu$s)",
    "t2": r"$T_2$ ($\mu$s)",
    "t2_star": r"$T_2^*$ ($\mu$s)",
    "t2_echo": r"$T_{2\mathrm{E}}$ ($\mu$s)",
    "frequency": r"$f_{01}$ (GHz)",
    "freq": r"$f_{01}$ (GHz)",
    "anharmonicity": r"$\alpha$ (MHz)",
    "readout_fidelity": r"$F_{\mathrm{RO}}$",
    "readout_error": r"$\varepsilon_{\mathrm{RO}}$",
    "cz_fidelity": r"$F_{\mathrm{CZ}}$",
    "iswap_fidelity": r"$F_{\mathrm{iSWAP}}$",
    "gate_fidelity": r"$F_{\mathrm{2Q}}$",
    "two_qubit_fidelity": r"$F_{\mathrm{2Q}}$",
    "cz_error": r"$\varepsilon_{\mathrm{CZ}}$",
    "iswap_error": r"$\varepsilon_{\mathrm{iSWAP}}$",
    "gate_error": r"$\varepsilon_{\mathrm{2Q}}$",
}

FIDELITY_KEYS = frozenset(
    {
        "cz_fidelity",
        "iswap_fidelity",
        "gate_fidelity",
        "two_qubit_fidelity",
        "readout_fidelity",
    }
)
ERROR_KEYS = frozenset(
    {
        "cz_error",
        "iswap_error",
        "gate_error",
        "readout_error",
    }
)


@dataclass
class QubitSite:
    """One physical qubit in the 2-D drawing plane."""

    qubit_id: str
    x: float
    y: float
    metrics: dict[str, float] = field(default_factory=dict)
    label: str | None = None
    grid_row: int | None = None
    grid_col: int | None = None


@dataclass
class CouplerSite:
    """Two-qubit coupler drawn at the midpoint of its endpoints."""

    coupler_id: str
    qubit_a: str
    qubit_b: str
    metrics: dict[str, float] = field(default_factory=dict)
    x: float | None = None
    y: float | None = None


@dataclass
class ChipLayout:
    """Planar chip graph: qubit sites, coupler edges, and named metrics."""

    name: str
    qubits: list[QubitSite]
    couplers: list[CouplerSite] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        ids = [q.qubit_id for q in self.qubits]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate qubit_id in ChipLayout")
        self._by_id = {q.qubit_id: q for q in self.qubits}
        for c in self.couplers:
            if c.qubit_a not in self._by_id or c.qubit_b not in self._by_id:
                raise ValueError(f"coupler {c.coupler_id} references unknown qubit")
            if c.x is None or c.y is None:
                a, b = self._by_id[c.qubit_a], self._by_id[c.qubit_b]
                c.x = 0.5 * (a.x + b.x)
                c.y = 0.5 * (a.y + b.y)

    def qubit(self, qubit_id: str) -> QubitSite:
        return self._by_id[qubit_id]

    def bounds(self, pad: float = 0.0) -> tuple[float, float, float, float]:
        xs = [q.x for q in self.qubits]
        ys = [q.y for q in self.qubits]
        if self.couplers:
            xs.extend(c.x for c in self.couplers if c.x is not None)
            ys.extend(c.y for c in self.couplers if c.y is not None)
        return (
            min(xs) - pad,
            max(xs) + pad,
            min(ys) - pad,
            max(ys) + pad,
        )

    def mean_spacing(self) -> float:
        if not self.couplers:
            if len(self.qubits) < 2:
                return 1.0
            pts = np.array([(q.x, q.y) for q in self.qubits], dtype=float)
            dmin = np.inf
            for i, p in enumerate(pts):
                delta = pts[i + 1 :] - p
                if len(delta) == 0:
                    continue
                dmin = min(dmin, float(np.min(np.hypot(delta[:, 0], delta[:, 1]))))
            return 1.0 if not np.isfinite(dmin) else dmin
        lengths = []
        for c in self.couplers:
            a, b = self._by_id[c.qubit_a], self._by_id[c.qubit_b]
            lengths.append(float(np.hypot(a.x - b.x, a.y - b.y)))
        return float(np.median(lengths)) if lengths else 1.0

    def set_qubit_metrics(self, key: str, values: Mapping[str, float]) -> None:
        for qid, val in values.items():
            self._by_id[qid].metrics[key] = float(val)

    def set_coupler_metrics(self, key: str, values: Mapping[str, float]) -> None:
        by_id = {c.coupler_id: c for c in self.couplers}
        by_pair = {tuple(sorted((c.qubit_a, c.qubit_b))): c for c in self.couplers}
        for name, val in values.items():
            if name in by_id:
                by_id[name].metrics[key] = float(val)
                continue
            if "__" in name:
                pair = tuple(sorted(name.split("__", 1)))
                if pair in by_pair:
                    by_pair[pair].metrics[key] = float(val)
                    continue
            raise KeyError(f"unknown coupler metric target {name!r}")

    def average_degree(self) -> float:
        if not self.qubits:
            return 0.0
        return 2.0 * len(self.couplers) / len(self.qubits)

    @classmethod
    def from_ascii(
        cls,
        diagram: str,
        *,
        name: str = "ascii-chip",
        connect: str = "4",
        notes: str = "",
        id_prefix: str = "q",
    ) -> ChipLayout:
        """Build a layout from a Cirq-style ASCII occupancy map.

        Alphanumeric characters are qubits; ``-``, ``.`` and spaces are empty.
        ``connect='4'`` links orthogonal neighbours; ``'8'`` also links diagonals.
        Qubit ids are assigned row-major as ``q000``, ``q001``, ...
        """
        lines = [line.rstrip("\n") for line in diagram.strip("\n").splitlines()]
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines:
            raise ValueError("empty ASCII diagram")

        occupied: dict[tuple[int, int], str] = {}
        qubits: list[QubitSite] = []
        index = 0
        for row, line in enumerate(lines):
            for col, char in enumerate(line):
                if char in EMPTY_DIAGRAM_CHARS:
                    continue
                qid = f"{id_prefix}{index:03d}"
                occupied[(row, col)] = qid
                qubits.append(
                    QubitSite(
                        qubit_id=qid,
                        x=float(col),
                        y=float(-row),
                        label=qid,
                        grid_row=row,
                        grid_col=col,
                    )
                )
                index += 1

        deltas = ((0, 1), (1, 0)) if connect == "4" else ((0, 1), (1, 0), (1, 1), (1, -1))
        couplers: list[CouplerSite] = []
        for (row, col), qid in occupied.items():
            for dr, dc in deltas:
                other = occupied.get((row + dr, col + dc))
                if other is None:
                    continue
                a, b = sorted((qid, other))
                couplers.append(
                    CouplerSite(
                        coupler_id=f"tc_{a}_{b}",
                        qubit_a=a,
                        qubit_b=b,
                    )
                )
        return cls(name=name, qubits=qubits, couplers=couplers, notes=notes)

    @classmethod
    def rectangular_grid(
        cls,
        n_rows: int,
        n_cols: int,
        *,
        name: str | None = None,
        id_prefix: str = "q",
    ) -> ChipLayout:
        """Axis-aligned n_rows × n_cols lattice with nearest-neighbour couplers."""
        if n_rows < 1 or n_cols < 1:
            raise ValueError("grid dimensions must be positive")
        rows = ["X" * n_cols for _ in range(n_rows)]
        title = name or f"{n_rows}x{n_cols} grid"
        return cls.from_ascii("\n".join(rows), name=title, id_prefix=id_prefix)


@dataclass
class TopologyFigure:
    """Return bundle from :func:`plot_chip_topology`."""

    fig: Figure
    ax: Axes
    qubit_mappable: ScalarMappable | None
    coupler_mappable: ScalarMappable | None
    qubit_cbar: Colorbar | None
    coupler_cbar: Colorbar | None


def _lookup_metric(metrics: Mapping[str, float], key: str) -> float | None:
    if key in metrics:
        return float(metrics[key])
    key_l = key.lower()
    for stored, val in metrics.items():
        if stored.lower() == key_l:
            return float(val)
    return None


def _metric_label(key: str, override: str | None) -> str:
    if override:
        return override
    return METRIC_LABELS.get(key, METRIC_LABELS.get(key.lower(), key.replace("_", " ")))


def _finite_values(sites: Sequence[QubitSite] | Sequence[CouplerSite], key: str) -> np.ndarray:
    vals = []
    for site in sites:
        v = _lookup_metric(site.metrics, key)
        if v is not None and np.isfinite(v):
            vals.append(v)
    return np.asarray(vals, dtype=float)


def _norm_for(
    values: np.ndarray,
    vmin: float | None,
    vmax: float | None,
    key: str,
) -> mcolors.Normalize:
    if values.size == 0:
        return mcolors.Normalize(0.0, 1.0)
    lo = float(np.min(values)) if vmin is None else float(vmin)
    hi = float(np.max(values)) if vmax is None else float(vmax)
    if lo == hi:
        pad = 0.05 * (abs(lo) if lo != 0 else 1.0)
        lo, hi = lo - pad, hi + pad
    if key.lower() in FIDELITY_KEYS and vmin is None and vmax is None:
        # Keep a readable high-fidelity window rather than stretching to 0–1.
        span = max(hi - lo, 1e-4)
        lo = max(0.0, lo - 0.15 * span)
        hi = min(1.0, hi + 0.15 * span)
    return mcolors.Normalize(lo, hi)


def _fidelity_formatter(value: float, _pos: int) -> str:
    if 0.0 <= value <= 1.0:
        return f"{100.0 * value:.2f}%"
    return f"{value:.3g}"


def _error_formatter(value: float, _pos: int) -> str:
    if 0.0 <= abs(value) < 0.01:
        return f"{value:.3f}"
    return f"{value:.3g}"


def _default_formatter(key: str):
    key_l = key.lower()
    if key_l in FIDELITY_KEYS:
        return _fidelity_formatter
    if key_l in ERROR_KEYS:
        return _error_formatter
    return None


def _draw_substrate(ax: Axes, xmin: float, xmax: float, ymin: float, ymax: float, pad: float) -> None:
    ax.add_patch(
        FancyBboxPatch(
            (xmin - pad, ymin - pad),
            (xmax - xmin) + 2 * pad,
            (ymax - ymin) + 2 * pad,
            boxstyle="round,pad=0,rounding_size=0.45",
            facecolor="#F6F7F9",
            edgecolor="#C8CCD4",
            linewidth=0.7,
            zorder=0,
        )
    )


def plot_chip_topology(
    layout: ChipLayout,
    *,
    qubit_metric: str | None = "t1",
    coupler_metric: str | None = "cz_fidelity",
    ax: Axes | None = None,
    preset: FigurePreset | str = "journal",
    qubit_cmap: str = "YlGnBu",
    coupler_cmap: str = "YlOrRd",
    qubit_vmin: float | None = None,
    qubit_vmax: float | None = None,
    coupler_vmin: float | None = None,
    coupler_vmax: float | None = None,
    qubit_label: str | None = None,
    coupler_label: str | None = None,
    show_labels: str | bool = False,
    label_size: float | None = None,
    show_bonds: bool = True,
    show_legend: bool = True,
    legend_labels: tuple[str, str] = ("Qubit", "Coupler"),
    show_substrate: bool = True,
    title: str | None = None,
    footnote: str | None = None,
    missing_color: str = "#D9DDE3",
    qubit_edgecolor: str = "#1B1E23",
    coupler_edgecolor: str = "#3A3F47",
    coupler_shape: str = "square",
    qubit_radius: float | None = None,
    coupler_size: float | None = None,
) -> TopologyFigure:
    """Draw a publication topology map.

    Parameters
    ----------
    qubit_metric, coupler_metric
        Metric keywords stored on each site (case-insensitive). ``None``
        draws that family in a uniform fill (topology-only).
    show_labels
        ``False``/``'none'``: no text.
        ``True``/``'id'``: qubit ids.
        ``'grid'``: ``(row, col)`` when available.
    coupler_shape
        ``'square'`` (default) or ``'rect'`` (elongated along the bond).
    """
    style = apply_publication_style(preset)
    created_fig = ax is None
    q_values = _finite_values(layout.qubits, qubit_metric) if qubit_metric else np.asarray([])
    c_values = _finite_values(layout.couplers, coupler_metric) if coupler_metric else np.asarray([])
    want_q_cbar = created_fig and qubit_metric is not None and q_values.size > 0
    want_c_cbar = created_fig and coupler_metric is not None and c_values.size > 0

    place_colorbars = False
    if ax is None:
        fig, ax, place_colorbars = _make_map_figure(style, want_q_cbar, want_c_cbar)
    else:
        fig = ax.figure

    spacing = layout.mean_spacing()
    q_radius = 0.29 * spacing if qubit_radius is None else qubit_radius
    c_side = 0.26 * spacing if coupler_size is None else coupler_size
    xmin, xmax, ymin, ymax = layout.bounds()
    substrate_pad = 0.72 * spacing
    substrate = (
        xmin - substrate_pad,
        xmax + substrate_pad,
        ymin - substrate_pad,
        ymax + substrate_pad,
    )

    if show_substrate:
        _draw_substrate(ax, xmin, xmax, ymin, ymax, pad=substrate_pad)

    if show_bonds:
        for c in layout.couplers:
            a = layout.qubit(c.qubit_a)
            b = layout.qubit(c.qubit_b)
            ax.plot(
                [a.x, b.x],
                [a.y, b.y],
                color="#C5CAD3",
                linewidth=0.95,
                solid_capstyle="round",
                zorder=1,
            )

    q_norm = _norm_for(q_values, qubit_vmin, qubit_vmax, qubit_metric or "")
    c_norm = _norm_for(c_values, coupler_vmin, coupler_vmax, coupler_metric or "")
    q_cmap = plt.get_cmap(qubit_cmap)
    c_cmap = plt.get_cmap(coupler_cmap)

    coupler_patches: list[Rectangle] = []
    coupler_faces: list[tuple[float, float, float, float]] = []
    missing_coupler_patches: list[Rectangle] = []
    for c in layout.couplers:
        assert c.x is not None and c.y is not None
        a = layout.qubit(c.qubit_a)
        b = layout.qubit(c.qubit_b)
        dx, dy = b.x - a.x, b.y - a.y
        if coupler_shape == "rect":
            along = 0.42 * spacing
            across = 0.16 * spacing
            if abs(dx) >= abs(dy):
                w, h = along, across
            else:
                w, h = across, along
        else:
            w = h = c_side
        rect = Rectangle((c.x - 0.5 * w, c.y - 0.5 * h), w, h, zorder=2)
        val = _lookup_metric(c.metrics, coupler_metric) if coupler_metric else None
        if coupler_metric is None:
            rect.set_facecolor("#F7F1E8")
            rect.set_edgecolor(coupler_edgecolor)
            rect.set_linewidth(0.55)
            ax.add_patch(rect)
        elif val is None or not np.isfinite(val):
            missing_coupler_patches.append(rect)
        else:
            coupler_patches.append(rect)
            coupler_faces.append(c_cmap(c_norm(val)))

    if coupler_patches:
        pc_c = PatchCollection(
            coupler_patches,
            facecolors=coupler_faces,
            edgecolors=coupler_edgecolor,
            linewidths=0.55,
            zorder=2,
        )
        ax.add_collection(pc_c)
    if missing_coupler_patches:
        ax.add_collection(
            PatchCollection(
                missing_coupler_patches,
                facecolors=missing_color,
                edgecolors=coupler_edgecolor,
                linewidths=0.55,
                zorder=2,
            )
        )

    qubit_patches: list[Circle] = []
    qubit_faces: list[tuple[float, float, float, float]] = []
    missing_qubit_patches: list[Circle] = []
    uniform_qubits: list[Circle] = []
    for q in layout.qubits:
        circ = Circle((q.x, q.y), q_radius, zorder=3)
        val = _lookup_metric(q.metrics, qubit_metric) if qubit_metric else None
        if qubit_metric is None:
            circ.set_facecolor("#EEF2F6")
            circ.set_edgecolor(qubit_edgecolor)
            circ.set_linewidth(0.7)
            uniform_qubits.append(circ)
        elif val is None or not np.isfinite(val):
            missing_qubit_patches.append(circ)
        else:
            qubit_patches.append(circ)
            qubit_faces.append(q_cmap(q_norm(val)))

    for circ in uniform_qubits:
        ax.add_patch(circ)
    if qubit_patches:
        ax.add_collection(
            PatchCollection(
                qubit_patches,
                facecolors=qubit_faces,
                edgecolors=qubit_edgecolor,
                linewidths=0.7,
                zorder=3,
            )
        )
    if missing_qubit_patches:
        ax.add_collection(
            PatchCollection(
                missing_qubit_patches,
                facecolors=missing_color,
                edgecolors=qubit_edgecolor,
                linewidths=0.7,
                zorder=3,
            )
        )

    label_mode = _normalize_label_mode(show_labels)
    if label_mode != "none":
        fs = style.font_size - 2.0 if label_size is None else label_size
        for q in layout.qubits:
            text = _site_label(q, label_mode)
            if not text:
                continue
            ax.text(
                q.x,
                q.y,
                text,
                ha="center",
                va="center",
                fontsize=fs,
                color="#111111",
                zorder=4,
                clip_on=True,
            )

    ax.set_aspect("equal")
    pad = 0.95 * spacing
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - pad, ymax + pad)
    ax.set_axis_off()
    if title:
        ax.set_title(title, pad=8)

    if show_legend:
        _add_shape_legend(ax, style.font_size, legend_labels, substrate, spacing)

    q_mappable = ScalarMappable(norm=q_norm, cmap=q_cmap) if qubit_metric and q_values.size else None
    c_mappable = ScalarMappable(norm=c_norm, cmap=c_cmap) if coupler_metric and c_values.size else None
    if q_mappable is not None:
        q_mappable.set_array(q_values)
    if c_mappable is not None:
        c_mappable.set_array(c_values)

    q_cbar = c_cbar = None
    if place_colorbars and (q_mappable is not None or c_mappable is not None):
        q_cbar, c_cbar = _place_scale_matched_colorbars(
            fig,
            ax,
            substrate,
            q_mappable if qubit_metric else None,
            c_mappable if coupler_metric else None,
            qubit_metric,
            coupler_metric,
            qubit_label,
            coupler_label,
        )

    if footnote:
        fig.text(0.01, 0.01, footnote, fontsize=style.font_size - 1.5, color="#5C6370", ha="left", va="bottom")

    return TopologyFigure(
        fig=fig,
        ax=ax,
        qubit_mappable=q_mappable,
        coupler_mappable=c_mappable,
        qubit_cbar=q_cbar,
        coupler_cbar=c_cbar,
    )


def _normalize_label_mode(show_labels: str | bool) -> str:
    if show_labels is False:
        return "none"
    if show_labels is True:
        return "id"
    mode = str(show_labels).lower()
    if mode not in {"none", "id", "grid"}:
        raise ValueError("show_labels must be False, True, 'none', 'id', or 'grid'")
    return mode


def _site_label(q: QubitSite, mode: str) -> str:
    if mode == "id":
        return q.label or q.qubit_id
    if mode == "grid" and q.grid_row is not None and q.grid_col is not None:
        return f"{q.grid_row},{q.grid_col}"
    return ""


def _add_shape_legend(
    ax: Axes,
    font_size: float,
    labels: tuple[str, str],
    substrate: tuple[float, float, float, float],
    spacing: float,
) -> None:
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="white",
            markeredgecolor="#1B1E23",
            markersize=7.0,
            label=labels[0],
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            color="none",
            markerfacecolor="white",
            markeredgecolor="#3A3F47",
            markersize=6.5,
            label=labels[1],
        ),
    ]
    x0, _x1, _y0, y1 = substrate
    # Sit in the empty top-left of the panel, clearly below the rounded rim.
    ax.legend(
        handles=handles,
        loc="upper left",
        bbox_to_anchor=(x0 + 0.55 * spacing, y1 - 0.85 * spacing),
        bbox_transform=ax.transData,
        borderaxespad=0.0,
        handletextpad=0.35,
        labelspacing=0.28,
        borderpad=0.15,
        fontsize=font_size - 0.5,
        frameon=False,
    )


def _make_map_figure(
    style: FigurePreset,
    want_q_cbar: bool,
    want_c_cbar: bool,
) -> tuple[Figure, Axes, bool]:
    n_bars = int(want_q_cbar) + int(want_c_cbar)
    fig = plt.figure(figsize=figure_size_inch(style))
    if n_bars == 0:
        ax = fig.add_axes((0.03, 0.05, 0.94, 0.92))
        return fig, ax, False
    # Right ~28% reserved so bars can sit beside the substrate.
    ax = fig.add_axes((0.02, 0.06, 0.68, 0.90))
    return fig, ax, True


def _data_to_figure(ax: Axes, x: float, y: float) -> tuple[float, float]:
    disp = ax.transData.transform((x, y))
    return tuple(ax.figure.transFigure.inverted().transform(disp))


def _place_scale_matched_colorbars(
    fig: Figure,
    ax: Axes,
    substrate: tuple[float, float, float, float],
    q_mappable: ScalarMappable | None,
    c_mappable: ScalarMappable | None,
    qubit_metric: str | None,
    coupler_metric: str | None,
    qubit_label: str | None,
    coupler_label: str | None,
) -> tuple[Colorbar | None, Colorbar | None]:
    """Place slim colorbars whose height matches the grey substrate."""
    fig.canvas.draw()
    _sx0, sx1, sy0, sy1 = substrate
    _fx0, fy0 = _data_to_figure(ax, sx1, sy0)
    fx1, fy1 = _data_to_figure(ax, sx1, sy1)
    height = fy1 - fy0
    if height <= 0:
        return None, None

    items: list[tuple[ScalarMappable, str, str | None]] = []
    if q_mappable is not None and qubit_metric:
        items.append((q_mappable, qubit_metric, qubit_label))
    if c_mappable is not None and coupler_metric:
        items.append((c_mappable, coupler_metric, coupler_label))
    if not items:
        return None, None

    bar_w = 0.014
    label_gutter = 0.058
    x = fx1 + 0.016
    bars: list[Colorbar] = []
    for mappable, key, label in items:
        cax = fig.add_axes((x, fy0, bar_w, height))
        bars.append(_fill_colorbar(fig, cax, mappable, key, label))
        x += bar_w + label_gutter

    q_cbar = bars[0] if q_mappable is not None and qubit_metric else None
    if q_cbar is None:
        c_cbar = bars[0] if bars else None
    else:
        c_cbar = bars[1] if len(bars) > 1 else None
    return q_cbar, c_cbar


def _fill_colorbar(
    fig: Figure,
    cax: Axes,
    mappable: ScalarMappable,
    key: str,
    label: str | None,
) -> Colorbar:
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(_metric_label(key, label), labelpad=4)
    cb.outline.set_linewidth(0.5)
    cb.ax.tick_params(length=2.0, width=0.5, pad=1.5)
    fmt = _default_formatter(key)
    if fmt is not None:
        cb.ax.yaxis.set_major_formatter(FuncFormatter(fmt))
    return cb


def save_topology_figure(
    fig: Figure,
    stem: str | Path,
    *,
    formats: Iterable[str] = ("pdf", "svg", "png"),
    dpi: int | None = None,
) -> list[Path]:
    """Write vector (PDF/SVG) plus optional raster copies next to ``stem``."""
    stem_path = Path(stem)
    stem_path.parent.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    save_kw: dict[str, object] = {"bbox_inches": "tight", "facecolor": "white", "edgecolor": "none"}
    if dpi is not None:
        save_kw["dpi"] = dpi
    for ext in formats:
        out = stem_path.with_suffix(f".{ext.lstrip('.')}")
        fig.savefig(out, **save_kw)
        written.append(out)
    return written
