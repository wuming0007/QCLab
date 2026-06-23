"""Manifest helpers for L9/OI (parse, view)."""

from __future__ import annotations

from qxtrl.ds import FileResultStore

from .models import ManifestView


def parse_run_id(run_id_or_ref: str) -> str:
    """MVP: only accept clean run_id or exact qxtrl://runs/<safe_run_id>/manifest.json .
    Reject anything with .. / \ or non-runs scheme.
    """
    if run_id_or_ref.startswith("qxtrl://"):
        if not run_id_or_ref.startswith("qxtrl://runs/") or not run_id_or_ref.endswith("/manifest.json"):
            raise ValueError("manifest ref must be qxtrl://runs/<run_id>/manifest.json")
        # extract
        prefix = "qxtrl://runs/"
        suffix = "/manifest.json"
        rid = run_id_or_ref[len(prefix):-len(suffix)]
        if not rid or ".." in rid or "/" in rid or "\\" in rid:
            raise ValueError("invalid run_id in manifest ref")
        return rid
    # plain run_id
    if "/" in run_id_or_ref or "\\" in run_id_or_ref or ".." in run_id_or_ref:
        raise ValueError("only logical run_id or qxtrl:// ref allowed")
    return run_id_or_ref


def show_manifest(run_id_or_ref: str, result_dir: str = "runs") -> ManifestView:
    run_id = parse_run_id(run_id_or_ref)
    manifest = FileResultStore(base_dir=result_dir).get_manifest(run_id)

    tm = getattr(manifest, "timing_metrics", {})
    if hasattr(tm, "model_dump"):
        tm_dict = tm.model_dump()
        timings = {k: float(v) for k, v in tm_dict.items() if isinstance(v, (int, float))}
    else:
        timings = {k: float(v) for k, v in dict(tm).items() if isinstance(v, (int, float))}

    return ManifestView(
        run_id=manifest.run_id,
        final_state=manifest.final_state,
        manifest_ref=run_id_or_ref,
        input_refs=dict(manifest.input_snapshots or {}),
        output_refs={k: [r.model_dump() for r in (v or [])] for k, v in (manifest.output_refs or {}).items()},
        timings=timings,
        diagnostics=(),
    )
