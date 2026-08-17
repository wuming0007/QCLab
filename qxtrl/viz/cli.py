"""CLI for publication chip-topology figures."""

from __future__ import annotations

import argparse
from pathlib import Path

from .topology import plot_chip_topology, save_topology_figure
from .willow import willow105_layout


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Draw a publication topology map. Circles are qubits; squares are "
            "couplers. Colour is bound to a metric keyword."
        )
    )
    parser.add_argument("--qubit-metric", default="t1", help="Qubit colour keyword, e.g. t1, t2, frequency")
    parser.add_argument(
        "--coupler-metric",
        default="cz_fidelity",
        help="Coupler colour keyword, e.g. cz_fidelity, cz_error, gate_fidelity",
    )
    parser.add_argument("--seed", type=int, default=0, help="RNG seed for illustrative Willow samples")
    parser.add_argument(
        "--out",
        default="figures/chip_topology/willow105",
        help="Output path stem (extensions are added)",
    )
    parser.add_argument("--preset", default="journal", choices=("journal", "slide"))
    parser.add_argument("--show-labels", default="none", choices=("none", "id", "grid"))
    parser.add_argument("--formats", default="pdf,svg,png", help="Comma-separated output formats")
    parser.add_argument(
        "--footnote",
        default="",
        help="Optional on-figure note. Journals usually put this in the caption instead.",
    )
    parser.add_argument(
        "--legend-zh",
        action="store_true",
        help="Use Chinese shape-legend labels (量子比特 / 耦合器)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> list[Path]:
    args = parse_args(argv)
    layout = willow105_layout(seed=args.seed)
    footnote = args.footnote if args.footnote else None
    legend = ("量子比特", "耦合器") if args.legend_zh else ("Qubit", "Coupler")
    result = plot_chip_topology(
        layout,
        qubit_metric=args.qubit_metric,
        coupler_metric=args.coupler_metric,
        preset=args.preset,
        show_labels=args.show_labels,
        legend_labels=legend,
        footnote=footnote,
    )
    stem = Path(args.out)
    if stem.name == "willow105" and (args.qubit_metric != "t1" or args.coupler_metric != "cz_fidelity"):
        stem = stem.with_name(f"willow105_{args.qubit_metric}_{args.coupler_metric}")
    written = save_topology_figure(
        result.fig,
        stem,
        formats=[f.strip() for f in args.formats.split(",") if f.strip()],
    )
    for path in written:
        print(path)
    return written
