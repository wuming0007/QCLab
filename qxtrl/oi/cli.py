"""Minimal L9 CLI using argparse (no extra deps).

Supports:
  python -m qxtrl.oi.cli run rabi --qubit q000 --json
  python -m qxtrl.oi.cli manifest show <run_id_or_ref> --json
"""

import argparse
import json
import sys
from typing import Any

from .sdk import run_rabi_virtual
from .models import RunRabiOptions
from .manifest import show_manifest
from .formatters import to_text as format_text
from pydantic import ValidationError as PydanticValidationError


def _print_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2, default=str))


def cmd_run_rabi(args: argparse.Namespace) -> int:
    if args.mode == "hardware":
        if args.json:
            _print_json({"error": "hardware mode not supported in MVP", "code": "OI-UNSUPPORTED-MODE"})
        else:
            print("hardware mode not supported in MVP")
        return 2
    try:
        options = RunRabiOptions(
            qubit_id=args.qubit,
            points=args.points,
            shots=args.shots,
            mode=args.mode,
            result_dir=args.result_dir,
        )
        summary = run_rabi_virtual(
            qubit_id=options.qubit_id,
            points=options.points,
            shots=options.shots,
            mode=options.mode,
            result_dir=options.result_dir,
        )

        if args.json:
            _print_json(summary.model_dump())
        else:
            print(format_text(summary))

        if summary.final_state == "succeeded":
            return 0
        else:
            return 3
    except PydanticValidationError as e:
        if args.json:
            _print_json({"error": str(e), "code": "OI-ARGUMENT-SCHEMA"})
        else:
            print(f"Error: {e}")
        return 2
    except ValueError as e:
        # e.g. qubit not in context, or other arg-like
        if args.json:
            _print_json({"error": str(e), "code": "OI-ARGUMENT-SCHEMA"})
        else:
            print(f"Error: {e}")
        return 2
    except Exception as e:
        if args.json:
            _print_json({"error": str(e), "code": "OI-RUNTIME-FAILED"})
        else:
            print(f"Error: {e}")
        return 3


def cmd_manifest_show(args: argparse.Namespace) -> int:
    try:
        view = show_manifest(args.run_id_or_ref, result_dir=args.result_dir)
        if args.json:
            _print_json(view.model_dump())
        else:
            print(f"Manifest {view.run_id} ({view.final_state})")
            print(f"  ref: {view.manifest_ref}")
        return 0
    except Exception as e:
        if args.json:
            _print_json({"error": str(e), "code": "OI-MANIFEST-NOT-FOUND"})
        else:
            print(f"Error: {e}")
        return 4


def cmd_report_export(args: argparse.Namespace) -> int:
    try:
        view = show_manifest(args.run_id_or_ref, result_dir=args.result_dir)
        # for simplicity, use summary from a run if possible, but here fake with view
        from .reports import export_markdown
        # minimal: use manifest view
        md = export_markdown(view, view)  # reuse
        if args.output:
            with open(args.output, "w") as f:
                f.write(md)
            print(f"Exported to {args.output}")
        else:
            print(md)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 5


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qxtrl.oi", description="QXtrl Operator Interfaces (MVP)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # run rabi
    p_run = sub.add_parser("run", help="Run experiment")
    p_rabi = p_run.add_subparsers(dest="subcmd", required=True)
    rabi = p_rabi.add_parser("rabi", help="Run Rabi virtual")
    rabi.add_argument("--qubit", default="q000")
    rabi.add_argument("--points", type=int, default=21)
    rabi.add_argument("--shots", type=int, default=1024)
    rabi.add_argument("--mode", default="virtual", choices=["virtual", "dry_run", "hardware"])
    rabi.add_argument("--result-dir", default="runs")
    rabi.add_argument("--json", action="store_true")
    rabi.set_defaults(func=cmd_run_rabi)

    # manifest show
    p_manifest = sub.add_parser("manifest", help="Manifest operations")
    p_msub = p_manifest.add_subparsers(dest="subcmd", required=True)
    show = p_msub.add_parser("show", help="Show manifest")
    show.add_argument("run_id_or_ref")
    show.add_argument("--result-dir", default="runs")
    show.add_argument("--json", action="store_true")
    show.set_defaults(func=cmd_manifest_show)

    # report export (basic for MVP-006)
    p_report = sub.add_parser("report", help="Report operations")
    p_rsub = p_report.add_subparsers(dest="subcmd", required=True)
    exp = p_rsub.add_parser("export", help="Export report")
    exp.add_argument("run_id_or_ref")
    exp.add_argument("--format", default="md", choices=["md"])
    exp.add_argument("--output", default=None)
    exp.add_argument("--result-dir", default="runs")
    exp.set_defaults(func=cmd_report_export)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
