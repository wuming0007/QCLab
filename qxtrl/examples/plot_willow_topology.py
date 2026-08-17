"""Publication-quality topology map of Google Willow (105 qubits).

Circles are qubits (default colour = T1). Squares are couplers
(default colour = CZ fidelity). Swap the metric keywords to plot any
other per-qubit or per-coupler field.

The occupancy grid is the public Cirq willow_pink / Willow105 layout.
Per-site colours are illustrative samples from published Chip-1 QEC
aggregates, not Google's measured device map.

Usage (from repo root)::

    PYTHONPATH=. python qxtrl/examples/plot_willow_topology.py
    PYTHONPATH=. python qxtrl/examples/plot_willow_topology.py --qubit-metric t2 --coupler-metric cz_error
    PYTHONPATH=. python -m qxtrl.viz --qubit-metric frequency --coupler-metric cz_fidelity
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from qxtrl.viz.cli import main


if __name__ == "__main__":
    main()
