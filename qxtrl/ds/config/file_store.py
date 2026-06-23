"""Minimal FileConfigStore for published snapshots (MVP read-only for L2/L4/L6).

Snapshots are L0 objects published via other tools. L5 only loads published ones.
"""

from __future__ import annotations

import json
from pathlib import Path


class FileConfigStore:
    """Very thin MVP: load published snapshots from a dir (e.g. config/snapshots)."""

    def __init__(self, snapshots_dir: str | Path = "config/snapshots"):
        self.dir = Path(snapshots_dir)

    def load_published(self, snapshot_id: str) -> dict:
        p = self.dir / f"{snapshot_id}.json"
        if not p.exists():
            p = self.dir / f"{snapshot_id}.yaml"  # allow
        if not p.exists():
            raise FileNotFoundError(f"published snapshot not found: {snapshot_id}")
        data = json.loads(p.read_text())
        if data.get("status") not in ("published", None):
            raise ValueError(f"snapshot not published: {snapshot_id}")
        return data

    # MVP stubs for write/propose (real would go through approval)
    def propose_patch(self, *a, **k):
        raise NotImplementedError("Config write via approval only (MVP stub)")

    def activate(self, *a, **k):
        raise NotImplementedError("Activate only via L6 + approval flow")
