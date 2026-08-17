"""Publication figure style for chip topology maps.

Defaults target a Nature-style double-column vector figure: TrueType
fonts in PDF/SVG, restrained spines, and print-sized type. Arial is
preferred when present; Helvetica / DejaVu Sans are fallbacks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib as mpl


JOURNAL_FONTS = ("Arial", "Helvetica", "DejaVu Sans")


@dataclass(frozen=True)
class FigurePreset:
    """Physical size and type scale for one output context."""

    name: str
    width_mm: float
    height_mm: float
    font_size: float
    axes_linewidth: float
    tick_width: float
    dpi: int


PRESET_JOURNAL = FigurePreset(
    name="journal",
    width_mm=183.0,  # Nature double-column
    height_mm=150.0,
    font_size=8.0,
    axes_linewidth=0.6,
    tick_width=0.6,
    dpi=600,
)

PRESET_SLIDE = FigurePreset(
    name="slide",
    width_mm=254.0,
    height_mm=190.0,
    font_size=14.0,
    axes_linewidth=1.0,
    tick_width=1.0,
    dpi=300,
)

PRESETS = {
    "journal": PRESET_JOURNAL,
    "slide": PRESET_SLIDE,
}


def mm_to_inch(mm: float) -> float:
    return mm / 25.4


def apply_publication_style(preset: FigurePreset | str = "journal") -> FigurePreset:
    """Set rcParams for vector, journal-quality output. Returns the preset used."""
    if isinstance(preset, str):
        try:
            preset = PRESETS[preset]
        except KeyError as exc:
            raise ValueError(f"unknown preset {preset!r}; expected one of {sorted(PRESETS)}") from exc

    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": preset.dpi,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
            "font.family": "sans-serif",
            "font.sans-serif": list(JOURNAL_FONTS),
            "font.size": preset.font_size,
            "axes.labelsize": preset.font_size,
            "axes.titlesize": preset.font_size + 1.0,
            "axes.linewidth": preset.axes_linewidth,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.labelsize": preset.font_size - 0.5,
            "ytick.labelsize": preset.font_size - 0.5,
            "xtick.major.width": preset.tick_width,
            "ytick.major.width": preset.tick_width,
            "legend.frameon": False,
            "legend.fontsize": preset.font_size - 0.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "text.usetex": False,
            "axes.unicode_minus": False,
            "mathtext.fontset": "dejavusans",
        }
    )
    return preset


def figure_size_inch(preset: FigurePreset) -> tuple[float, float]:
    return mm_to_inch(preset.width_mm), mm_to_inch(preset.height_mm)


def publication_rc(preset: FigurePreset | str = "journal") -> dict[str, Any]:
    """Return rcParams dict without mutating the global state (for tests)."""
    apply_publication_style(preset)
    return {k: mpl.rcParams[k] for k in ("pdf.fonttype", "svg.fonttype", "font.size")}
