"""Minimal report export for L9 (Markdown)."""

from __future__ import annotations

from typing import Any


def export_markdown(summary: Any, manifest: Any | None = None) -> str:
    lines = [
        "# QXtrl Rabi Report",
        "",
        f"- run_id: {getattr(summary, 'run_id', getattr(manifest, 'run_id', 'n/a'))}",
        f"- state: {getattr(summary, 'final_state', getattr(manifest, 'final_state', 'n/a'))}",
        f"- manifest: {getattr(summary, 'manifest_ref', getattr(manifest, 'manifest_ref', 'n/a'))}",
        "",
        "## Analysis",
        "",
        str(getattr(summary, 'analysis_summary', {})),
    ]
    if manifest:
        lines.append("\n## Timings")
        tm = getattr(manifest, 'timings', getattr(manifest, 'timing_metrics', {}))
        lines.append(str(tm))
        lines.append("\n## Diagnostics (from manifest view)")
        diags = getattr(manifest, 'diagnostics', ())
        lines.append(str(diags) if diags else "[]")
    return "\n".join(lines)
