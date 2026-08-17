"""Chip topology visualization helpers (used by L9 figures and notebooks).

Not a new architecture layer. Layouts and metrics stay independent of L0
control contracts: public examples are not usable for hardware execution.
"""

from .style import PRESET_JOURNAL, PRESET_SLIDE, PRESETS, FigurePreset, apply_publication_style
from .topology import (
    ChipLayout,
    CouplerSite,
    QubitSite,
    TopologyFigure,
    plot_chip_topology,
    save_topology_figure,
)
from .willow import WILLOW105_DIAGRAM, WILLOW_CAPTION, willow105_layout

__all__ = [
    "ChipLayout",
    "CouplerSite",
    "FigurePreset",
    "PRESET_JOURNAL",
    "PRESET_SLIDE",
    "PRESETS",
    "QubitSite",
    "TopologyFigure",
    "WILLOW105_DIAGRAM",
    "WILLOW_CAPTION",
    "apply_publication_style",
    "plot_chip_topology",
    "save_topology_figure",
    "willow105_layout",
]
