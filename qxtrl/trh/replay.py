"""L7/TRH Manifest replay (MVP: inspect + basic virtual rerun).

Per design: build ReplayPlan from L5 manifest, replay inspect.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from qxtrl.ds import FileResultStore  # L5

from .models import (
    TRHDiagnostic,
    ReplayRequest,
    ReplayPlan,
    ReplayResult,
)


def _parse_manifest_ref(ref: str) -> str:
    """Strict parser, similar to L9. Returns clean run_id or raises."""
    if ref.startswith("qxtrl://"):
        if not ref.startswith("qxtrl://runs/") or not ref.endswith("/manifest.json"):
            raise ValueError("manifest ref must be qxtrl://runs/<run_id>/manifest.json")
        rid = ref[len("qxtrl://runs/") : -len("/manifest.json")]
        if not rid or ".." in rid or "/" in rid or "\\" in rid:
            raise ValueError("invalid run_id in ref")
        return rid
    if "/" in ref or "\\" in ref or ".." in ref or not ref:
        raise ValueError("only logical run_id or qxtrl://runs/<id>/manifest.json allowed")
    return ref


def _extract_run_id_from_logical(logical: str) -> str | None:
    """Return the run_id segment from qxtrl://runs/<run_id>/... or None."""
    if not logical or not logical.startswith("qxtrl://runs/"):
        return None
    rest = logical[len("qxtrl://runs/"):]
    parts = rest.split("/", 1)
    return parts[0] if parts and parts[0] else None


def _check_dataset_file(base_dir: str, run_id: str, ref: Any) -> tuple[bool, str | None, str | None]:
    """Return (exists, actual_hash or None, error or None).

    Enforces:
    - DatasetRef belongs to the *source* manifest's run_id (no cross-run refs allowed).
    - content_hash must be "sha256:" + 16 or 64 lowercase hex chars (per L5 DatasetRef).
    - Hash comparison is exact match. Computes full digest then selects 16 or 64 truncation
      based on the *expected* length in the ref (supports both v0.1 16-char and future 64-char).
    """
    try:
        if isinstance(ref, str):
            logical = ref
            expected = ""
            ref_run_id = ""
        elif isinstance(ref, dict):
            logical = ref.get("logical_uri", "") or ""
            expected = ref.get("content_hash", "") or ""
            ref_run_id = ref.get("run_id", "") or ""
        else:
            logical = getattr(ref, "logical_uri", "") or ""
            expected = getattr(ref, "content_hash", "") or ""
            ref_run_id = getattr(ref, "run_id", "") or ""

        if not logical.startswith("qxtrl://runs/"):
            return False, None, f"non-qxtrl logical uri: {logical}"

        # 1. Ownership check (P1-001): uri run_id and/or ref.run_id must match source run_id
        uri_run = _extract_run_id_from_logical(logical)
        if uri_run and uri_run != run_id:
            return False, None, f"cross-run dataset ref: uri run_id={uri_run} != manifest {run_id}"
        if ref_run_id and ref_run_id != run_id:
            return False, None, f"cross-run dataset ref: ref.run_id={ref_run_id} != manifest {run_id}"

        rel = logical[len("qxtrl://runs/"):]
        if ".." in rel or rel.startswith(("/", "\\")):
            return False, None, "unsafe path traversal in dataset logical_uri"
        full_path = Path(base_dir) / rel
        if not full_path.exists() or not full_path.is_file():
            return False, None, "dataset file missing"

        content = full_path.read_bytes()
        full_digest = hashlib.sha256(content).hexdigest()

        # 2. Strict format + length-aware exact match (supports 16-char MVP and 64-char)
        if not expected or expected == "sha256:":
            return True, "sha256:" + full_digest[:16], "malformed content_hash (empty or 'sha256:')"
        if not expected.startswith("sha256:"):
            return True, "sha256:" + full_digest[:16], f"malformed content_hash (no sha256: prefix): {expected}"
        hexp = expected[7:]
        if len(hexp) not in (16, 64) or not all(c in "0123456789abcdef" for c in hexp):
            return True, "sha256:" + full_digest[:16], f"malformed content_hash format: {expected}"

        if len(hexp) == 16:
            actual = "sha256:" + full_digest[:16]
        else:
            actual = "sha256:" + full_digest

        if actual != expected:
            return True, actual, f"hash mismatch expected {expected} got {actual}"

        return True, actual, None
    except Exception as e:
        return False, None, str(e)


def build_replay_plan(request: ReplayRequest) -> ReplayPlan:
    """Build inspect plan from manifest ref. Uses current L5 RunManifest structure."""
    try:
        clean_run_id = _parse_manifest_ref(request.run_id_or_manifest_ref)
    except Exception as e:
        diag = TRHDiagnostic(
            severity="error",
            code="TRH-INPUT-SCHEMA",
            message=f"invalid manifest ref: {e}",
        )
        return ReplayPlan(
            replay_id=request.replay_id,
            source_run_id="invalid",
            source_manifest_ref="invalid",
            mode=request.mode,
            diagnostics=(diag,),
        )

    try:
        store = FileResultStore(base_dir=request.result_dir)
        manifest = store.get_manifest(clean_run_id)
    except Exception as e:
        diag = TRHDiagnostic(
            severity="error",
            code="TRH-MANIFEST-NOT-FOUND",
            message=f"manifest not found: {e}",
        )
        return ReplayPlan(
            replay_id=request.replay_id,
            source_run_id=clean_run_id,
            source_manifest_ref=request.run_id_or_manifest_ref,
            mode=request.mode,
            diagnostics=(diag,),
        )

    diags = []
    input_refs = {}
    if hasattr(manifest, "experiment") and manifest.experiment:
        input_refs["spec"] = manifest.experiment.spec_id
    if hasattr(manifest, "input_snapshots"):
        input_refs.update(manifest.input_snapshots)

    # Keep both: str uris for the public plan, and original DatasetRef objects for real hash/existence checks
    output_refs: dict[str, list[str]] = {}
    dataset_ref_objects: dict[str, list] = {}
    if hasattr(manifest, "output_refs") and manifest.output_refs:
        for k, v in manifest.output_refs.items():
            refs = list(v) if v else []
            dataset_ref_objects[k] = refs
            output_refs[k] = [str(getattr(r, "logical_uri", r)) for r in refs]

    compile_info = {}
    if hasattr(manifest, "compile") and manifest.compile:
        c = manifest.compile
        compile_info = {
            "bundle_id": c.bundle_id or "",
            "bundle_hash": c.bundle_hash or "",
            "pulse_ir_hash": c.pulse_ir_hash or "",
        }
        if not c.bundle_id:
            diags.append(TRHDiagnostic(severity="warning", code="TRH-MANIFEST-INCOMPLETE", message="missing compile.bundle_id"))

    if not input_refs.get("spec"):
        diags.append(TRHDiagnostic(severity="warning", code="TRH-MANIFEST-INCOMPLETE", message="missing experiment.spec_id"))

    if not output_refs:
        diags.append(TRHDiagnostic(severity="warning", code="TRH-MANIFEST-INCOMPLETE", message="missing output_refs"))

    if request.require_hash_check and (not compile_info.get("bundle_hash") or not compile_info.get("pulse_ir_hash")):
        diags.append(TRHDiagnostic(severity="error", code="TRH-MANIFEST-INCOMPLETE", message="missing bundle_hash or pulse_ir_hash for require_hash_check"))

    # Hash / dataset checks if required: use original ref objects (carry content_hash)
    if request.require_hash_check:
        for group, refs in dataset_ref_objects.items():
            for ref in refs:
                exists, actual, err = _check_dataset_file(request.result_dir, clean_run_id, ref)
                if not exists or err:
                    msg = err or "dataset missing"
                    if "cross-run" in msg or "malformed" in msg:
                        code = "TRH-DATASET-REF-MISMATCH"
                    elif not exists:
                        code = "TRH-DATASET-NOT-FOUND"
                    else:
                        code = "TRH-HASH-MISMATCH"
                    diags.append(TRHDiagnostic(severity="error", code=code, message=msg))
        # (second compile check removed to avoid duplicate TRH-MANIFEST-INCOMPLETE diagnostics)

    # For success case, require non-empty core refs
    has_core = bool(input_refs.get("spec")) and bool(output_refs)
    if request.mode == "inspect" and not has_core:
        # still allow inspect but mark
        pass

    plan = ReplayPlan(
        replay_id=request.replay_id,
        source_run_id=clean_run_id,
        source_manifest_ref=request.run_id_or_manifest_ref,
        mode=request.mode,
        required_input_refs=input_refs,
        required_output_refs=output_refs,
        expected_hashes=compile_info,
        diagnostics=tuple(diags),
    )
    return plan


def replay_manifest(request: ReplayRequest) -> ReplayResult:
    """MVP entry: inspect first. replay_virtual / recorded / compare return rejected until implemented."""
    plan = build_replay_plan(request)

    supported_modes = ("inspect",)
    if request.mode not in supported_modes:
        diag = TRHDiagnostic(
            severity="error",
            code="TRH-UNSUPPORTED-MODE",
            message=f"{request.mode} not implemented in v0.1",
        )
        return ReplayResult(
            replay_id=request.replay_id,
            source_run_id=plan.source_run_id,
            final_state="rejected",
            mode=request.mode,
            plan=plan,
            diagnostics=(diag,) + plan.diagnostics,
        )

    has_error = any(d.severity == "error" for d in plan.diagnostics)
    # Incomplete codes are blocking for success only when require_hash_check (or if they were emitted as error)
    has_blocking_incomplete = any(
        (d.code in ("TRH-MANIFEST-INCOMPLETE", "TRH-DATASET-NOT-FOUND", "TRH-HASH-MISMATCH", "TRH-DATASET-REF-MISMATCH"))
        and (request.require_hash_check or d.severity == "error")
        for d in plan.diagnostics
    )

    if has_error or has_blocking_incomplete:
        return ReplayResult(
            replay_id=request.replay_id,
            source_run_id=plan.source_run_id,
            final_state="rejected",
            mode=request.mode,
            plan=plan,
            diagnostics=plan.diagnostics,
        )

    # inspect succeeds for structural view; warnings (e.g. missing hashes) visible in diagnostics when !require
    final = "succeeded"
    core_present = bool(plan.required_input_refs.get("spec")) and bool(plan.required_output_refs)
    output = {"mode": request.mode, "inspected": True, "core_refs_present": core_present, "hash_check_performed": request.require_hash_check}

    return ReplayResult(
        replay_id=request.replay_id,
        source_run_id=plan.source_run_id,
        final_state=final,  # type: ignore
        mode=request.mode,
        plan=plan,
        output_summary=output,
        diagnostics=plan.diagnostics,
    )
