"""Simple text / json formatters for L9."""

from __future__ import annotations

import json
from typing import Any


def to_text(summary: Any) -> str:
    return (
        "QXtrl Rabi run completed\n"
        f"run_id: {getattr(summary, 'run_id', 'n/a')}\n"
        f"state: {getattr(summary, 'final_state', 'n/a')}\n"
        f"manifest: {getattr(summary, 'manifest_ref', 'n/a')}\n"
        f"duration_ms: {getattr(summary, 'total_duration_ms', 'n/a')}\n"
    )


def to_json(summary: Any) -> str:
    if hasattr(summary, "model_dump"):
        data = summary.model_dump()
    else:
        data = dict(summary) if isinstance(summary, dict) else {"value": str(summary)}
    return json.dumps(data, indent=2, default=str)
