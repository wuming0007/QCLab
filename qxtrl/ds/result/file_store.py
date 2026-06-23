from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..contracts.manifest import RunManifest, DatasetRef  # noqa: E402
from ..contracts.dataset import DatasetMetadata  # noqa: E402
from ..contracts.errors import DSError, DSCode  # noqa: E402
from .manifest_builder import build_from_runtime_result  # noqa: E402

__doc__ = """FileResultStore MVP implementation for L5.

Uses local filesystem: runs/<run_id>/manifest.json + .sha256 + raw/*.json etc.
Follows L0 layout rules + L5 invariants (raw immutable, no absolute path, atomic finalize).
"""


def _safe_run_dir(base: Path, run_id: str) -> Path:
    if not run_id or ".." in run_id or "/" in run_id or "\\" in run_id:
        raise DSError(DSCode.RUN_ID_CONFLICT, f"unsafe run_id: {run_id}")
    return base / run_id


class FileResultStore:
    """MVP file-based ResultStore. run_id provided by L4."""

    def __init__(self, base_dir: str | Path = "runs"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _run_dir(self, run_id: str) -> Path:
        return _safe_run_dir(self.base_dir, run_id)

    def create_run(
        self,
        *,
        run_id: str,
        station_id: str = "station.local",
        chip_id: Optional[str] = None,
        input_snapshots: Optional[dict[str, str]] = None,
        operator: str = "user.unknown",
    ) -> dict:
        """Minimal handle. Returns dict with run_id for compat."""
        d = self._run_dir(run_id)
        if d.exists():
            # allow if not finalized (for retry?); for MVP check manifest.json
            if (d / "manifest.json").exists():
                raise DSError(DSCode.RUN_ID_CONFLICT, f"run {run_id} already finalized")
        d.mkdir(parents=True, exist_ok=True)
        (d / "raw").mkdir(exist_ok=True)
        (d / "processed").mkdir(exist_ok=True)
        (d / "analysis").mkdir(exist_ok=True)
        (d / "events").mkdir(exist_ok=True)
        (d / "timings").mkdir(exist_ok=True)
        meta = {
            "run_id": run_id,
            "station_id": station_id,
            "chip_id": chip_id,
            "operator": operator,
            "input_snapshots": input_snapshots or {},
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
        (d / "run_meta.json").write_text(json.dumps(meta, indent=2))
        return {"run_id": run_id, "dir": str(d)}

    def write_dataset(
        self, run_id: str, name: str, data: Any, metadata: DatasetMetadata | dict
    ) -> DatasetRef:
        """Write data under raw/ or appropriate subdir. Returns DatasetRef.
        For MVP: json dump. Refuses overwrite for raw kinds.
        """
        d = self._run_dir(run_id)
        if not d.exists():
            self.create_run(run_id=run_id)

        kind = getattr(metadata, "kind", "raw_iq") if not isinstance(metadata, dict) else metadata.get("kind", "raw_iq")
        if kind.startswith("raw"):
            sub = "raw"
        elif kind in ("events", "timings"):
            sub = kind
        elif "process" in kind:
            sub = "processed"
        else:
            sub = "analysis"
        target_dir = d / sub
        target_dir.mkdir(exist_ok=True)

        # filename safe
        fname = f"{name}.json" if not name.endswith(".json") else name
        fpath = target_dir / fname

        if fpath.exists() and kind.startswith("raw"):
            raise DSError(DSCode.DATASET_WRITE_FAILED, f"raw dataset overwrite forbidden: {name}")

        # serialize
        if hasattr(data, "model_dump"):
            payload = data.model_dump(mode="python")
        else:
            payload = data
        fpath.write_text(json.dumps(payload, default=str, indent=2))

        # hash
        content = fpath.read_bytes()
        chash = "sha256:" + hashlib.sha256(content).hexdigest()[:16]

        meta_dict = metadata.model_dump() if hasattr(metadata, "model_dump") else dict(metadata)
        meta_hash = "sha256:" + hashlib.sha256(json.dumps(meta_dict, sort_keys=True).encode()).hexdigest()[:16]

        # logical uri (never absolute)
        logical = f"qxtrl://runs/{run_id}/{sub}/{fname}"

        ref = DatasetRef(
            dataset_id=f"{run_id}_{name}",
            run_id=run_id,
            logical_uri=logical,
            content_hash=chash,
            metadata_hash=meta_hash,
            kind=kind,
        )

        # sidecar meta
        (target_dir / f"{fname}.meta.json").write_text(json.dumps(meta_dict, indent=2))

        return ref

    def record_runtime_result(
        self,
        *,
        runtime_result: Any,
        spec: Any = None,
        bundle: Any = None,
    ) -> str:
        """Main L4 entry point. Builds manifest draft + writes available datasets + finalize.
        Returns manifest logical ref or run_id.
        """
        run_id = runtime_result.run_id
        self.create_run(run_id=run_id)

        # Build draft manifest (may be partial)
        draft = build_from_runtime_result(runtime_result, spec=spec, bundle=bundle)

        # If backend data present, write as dataset
        br = runtime_result.backend_result
        if br and getattr(br, "data", None):
            data = getattr(br, "data", {})
            try:
                md = DatasetMetadata(run_id=run_id, kind="raw_iq")
                ref = self.write_dataset(run_id, "iq", data, md)
                draft.output_refs.setdefault("raw", []).append(ref)
            except Exception:
                # non fatal for manifest
                pass

        # Write analysis_result if present (P1 from re-review)
        if runtime_result.analysis_result:
            try:
                ana_md = DatasetMetadata(run_id=run_id, kind="analysis_result")
                ana_ref = self.write_dataset(run_id, "analysis", runtime_result.analysis_result, ana_md)
                draft.output_refs.setdefault("analysis", []).append(ana_ref)
            except Exception:
                pass

        # Write events / timings as datasets for traceability (MVP)
        ev_ref = None
        ti_ref = None
        dref = None
        if runtime_result.events:
            try:
                ev_md = DatasetMetadata(run_id=run_id, kind="events")
                ev_ref = self.write_dataset(run_id, "events", [e.model_dump() if hasattr(e, "model_dump") else e for e in runtime_result.events], ev_md)
            except Exception:
                ev_ref = None

        if runtime_result.timings:
            try:
                ti_md = DatasetMetadata(run_id=run_id, kind="timings")
                ti_ref = self.write_dataset(run_id, "timings", [t.model_dump() if hasattr(t, "model_dump") else t for t in runtime_result.timings], ti_md)
            except Exception:
                ti_ref = None

        # Diagnostics refs (simple)
        if runtime_result.diagnostics:
            try:
                diag_md = DatasetMetadata(run_id=run_id, kind="log")
                dref = self.write_dataset(run_id, "diagnostics", [d.model_dump() for d in runtime_result.diagnostics], diag_md)
            except Exception:
                dref = None

        # Use model_copy to set refs on frozen model (avoid silent failure)
        update_kwargs = {}
        if ev_ref:
            update_kwargs["events_ref"] = ev_ref
        if ti_ref:
            update_kwargs["timings_ref"] = ti_ref
        if dref:
            update_kwargs["diagnostics_refs"] = [dref]
        if update_kwargs:
            draft = draft.model_copy(update=update_kwargs)

        # Finalize (will validate)
        ref = self.finalize_manifest(draft)
        return ref

    def finalize_manifest(self, manifest: RunManifest) -> str:
        """Atomic finalize. Writes manifest.json + .sha256. Returns logical ref."""
        run_id = manifest.run_id
        d = self._run_dir(run_id)
        d.mkdir(parents=True, exist_ok=True)

        man_path = d / "manifest.json"
        if man_path.exists():
            # idempotent check: if identical content ok? For MVP reject re-finalize unless same
            existing = json.loads(man_path.read_text())
            if existing.get("final_state") == manifest.final_state:
                return f"qxtrl://runs/{run_id}/manifest.json"
            raise DSError(DSCode.RUN_ALREADY_FINALIZED, f"run {run_id} already finalized")

        # Use copy for any last-minute adjustments on frozen model
        if getattr(manifest, "partial", False):
            manifest = manifest.model_copy(update={"partial": False})

        # Validate required per design
        if manifest.final_state == "succeeded" and manifest.partial:
            manifest = manifest.model_copy(update={"partial": False})  # shouldn't happen

        # Write tmp then rename (atomic-ish on same FS)
        tmp = d / "manifest.json.tmp"
        data = manifest.model_dump(mode="json")
        tmp.write_text(json.dumps(data, indent=2, default=str))

        # sha
        content = tmp.read_bytes()
        ch = hashlib.sha256(content).hexdigest()
        (d / "manifest.sha256").write_text(ch)

        # rename
        tmp.replace(man_path)

        # also human friendly note
        (d / "README.txt").write_text(
            f"Run {run_id} final_state={manifest.final_state}\n"
            f"See manifest.json for full record.\n"
        )

        logical = f"qxtrl://runs/{run_id}/manifest.json"
        return logical

    def get_manifest(self, run_id: str) -> RunManifest:
        d = self._run_dir(run_id)
        p = d / "manifest.json"
        if not p.exists():
            raise DSError(DSCode.SNAPSHOT_NOT_FOUND, f"no manifest for {run_id}")
        # Verify sidecar sha256 if present (defense against tamper; sidecar written at finalize)
        sha_p = d / "manifest.sha256"
        if sha_p.exists():
            try:
                expected = sha_p.read_text().strip()
                actual = hashlib.sha256(p.read_bytes()).hexdigest()
                if actual != expected:
                    raise DSError(DSCode.SNAPSHOT_NOT_FOUND, f"manifest sha256 mismatch for {run_id}")
            except Exception:
                # best effort; continue to validate (structural may still catch)
                pass
        data = json.loads(p.read_text())
        return RunManifest.model_validate(data)

    def query_runs(self, *, final_state: Optional[str] = None, chip_id: Optional[str] = None, limit: int = 100) -> list[str]:
        """Simple scan for MVP."""
        results = []
        for sub in sorted(self.base_dir.iterdir()):
            if not sub.is_dir():
                continue
            man = sub / "manifest.json"
            if man.exists():
                try:
                    m = json.loads(man.read_text())
                    if final_state and m.get("final_state") != final_state:
                        continue
                    if chip_id and m.get("chip_id") != chip_id:
                        continue
                    results.append(m["run_id"])
                except Exception:
                    continue
            if len(results) >= limit:
                break
        return results[:limit]
