"""VirtualExecutionBackend for L3/EB MVP.

Wraps the existing L7 virtual runner (trh) after verifying the bundle using
the L2 verify_compiled_bundle tool.

This demonstrates the L3 contract and the value of the shared verify tool.
"""

from __future__ import annotations

import uuid
from typing import Any

from qxtrl.cpir import verify_compiled_bundle, CompiledBundle
from qxtrl.trh import run_rabi_virtual_typed
from qxtrl.trh.models import (
    TwinModelRef,
    VirtualQPUConfig,
    VirtualRunRequest,
    VirtualRunResult,
)
from .models import (
    BackendSubmitRequest,
    BackendCapability,
    BackendRunResult,
    BackendDiagnostic,
    BackendEvent,
    ExecutionBackend,
)


class VirtualExecutionBackend(ExecutionBackend):
    """MVP Virtual backend for Rabi experiments.

    Usage:
        backend = VirtualExecutionBackend()
        result = backend.submit(request)   # request.bundle is a CompiledBundle (or dict)
    """

    backend_id: str = "backend.virtual.rabi_mvp"

    def describe_capability(self) -> BackendCapability:
        return BackendCapability(
            backend_id=self.backend_id,
            backend_kind="virtual",
            supported_bundle_versions=("qxtrl.cpir.CompiledBundle/v0.1",),
            supported_result_levels=("integrated_iq",),
            max_points=None,
            supports_cancel=False,
            supports_fault_injection=True,
        )

    def validate_bundle(self, bundle: CompiledBundle | dict[str, Any]) -> dict[str, Any]:
        """Entry point verification. Delegates to L2's verify_compiled_bundle.
        Returns a small report; raises on invalid.
        """
        verified = verify_compiled_bundle(bundle)
        return {
            "valid": True,
            "bundle_id": verified.bundle_id,
            "bundle_hash": verified.bundle_hash,
            "pulse_ir_hash": verified.pulse_ir.content_hash,
            "l0_refs_count": len(verified.l0_refs),
        }

    def submit(self, request: BackendSubmitRequest | dict[str, Any]) -> BackendRunResult:
        """Main entry. Validates request + bundle, runs virtual, returns result."""
        def _evt(stage: str, state: str, t: float, details: dict[str, Any] | None = None) -> BackendEvent:
            return BackendEvent(
                event_id=str(uuid.uuid4()),
                run_id=getattr(request, "run_id", "unknown") if hasattr(request, "run_id") else "unknown",
                backend_id=self.backend_id,
                stage=stage,  # type: ignore
                state=state,  # type: ignore
                t_rel_ms=t,
                details=details or {},
            )

        events: list[BackendEvent] = []

        try:
            if isinstance(request, dict):
                request = BackendSubmitRequest.model_validate(request)
        except Exception as e:
            diag = BackendDiagnostic(
                severity="error",
                code="EB-BUNDLE-SCHEMA",
                message=f"Request validation failed (possible raw non-bundle input): {e}",
                stage="validating",
            )
            events.append(_evt("validating", "failed", 0.0, {"error": str(e)}))
            return BackendRunResult(
                run_id=getattr(request, "run_id", "unknown") if not isinstance(request, dict) else request.get("run_id", "unknown"),
                backend_id=self.backend_id,
                final_state="rejected",
                bundle_id="unknown",
                bundle_hash="",
                pulse_ir_hash="",
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        if request.backend_id != self.backend_id:
            diag = BackendDiagnostic(
                severity="error",
                code="EB-UNSUPPORTED-BACKEND",
                message=f"backend_id mismatch: expected {self.backend_id}, got {request.backend_id}",
                stage="validating",
            )
            events.append(_evt("validating", "failed", 0.0, {"expected_backend_id": self.backend_id, "received": request.backend_id}))
            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="rejected",
                bundle_id=getattr(request.bundle, "bundle_id", "unknown") if hasattr(request, "bundle") else "unknown",
                bundle_hash=getattr(request.bundle, "bundle_hash", "") if hasattr(request, "bundle") else "",
                pulse_ir_hash="",
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        if request.mode not in ("virtual", "dry_run"):
            diag = BackendDiagnostic(
                severity="error",
                code="EB-UNSUPPORTED-BACKEND",
                message=f"unsupported mode: {request.mode}",
                stage="validating",
            )
            events.append(_evt("validating", "failed", 0.0, {"mode": request.mode}))
            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="rejected",
                bundle_id=getattr(request.bundle, "bundle_id", "unknown") if hasattr(request, "bundle") else "unknown",
                bundle_hash=getattr(request.bundle, "bundle_hash", "") if hasattr(request, "bundle") else "",
                pulse_ir_hash="",
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        # 1. Use the shared L2 verify tool (the point of the addition)
        try:
            verified = verify_compiled_bundle(request.bundle)
            events.append(_evt("validating", "succeeded", 0.0))
        except Exception as e:
            # Per design: failures return structured result + diagnostic, not raw exception
            code = "EB-BUNDLE-VERIFY"
            if "hash mismatch" in str(e).lower():
                code = "EB-BUNDLE-HASH"
            elif "schema" in str(e).lower() or "validation" in str(e).lower():
                code = "EB-BUNDLE-SCHEMA"
            diag = BackendDiagnostic(
                severity="error",
                code=code,
                message=f"Bundle verification failed: {e}",
                stage="validating",
            )
            events.append(_evt("validating", "failed", 0.0, {"error": str(e)}))
            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="rejected",
                bundle_id=getattr(getattr(request, 'bundle', None), 'bundle_id', 'unknown'),
                bundle_hash=getattr(getattr(request, 'bundle', None), 'bundle_hash', ''),
                pulse_ir_hash="",
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        # L3 capability gate (result level check)
        cap = self.describe_capability()
        unsupported_levels = []
        for win in getattr(verified.pulse_ir, "acquisition_windows", []):
            rl = getattr(win, "result_level", None)
            if rl and rl not in cap.supported_result_levels:
                unsupported_levels.append(rl)
        if unsupported_levels:
            diag = BackendDiagnostic(
                severity="error",
                code="EB-UNSUPPORTED-RESULT-LEVEL",
                message=f"Unsupported result levels: {unsupported_levels}",
                stage="validating",
            )
            events.append(_evt("validating", "failed", 0.1, {"unsupported": unsupported_levels}))
            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="rejected",
                bundle_id=verified.bundle_id,
                bundle_hash=verified.bundle_hash,
                pulse_ir_hash=verified.pulse_ir.content_hash,
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        # L3 L0 refs gate (strict for MVP)
        if len(verified.l0_refs) < 4:
            diag = BackendDiagnostic(
                severity="error",
                code="EB-BUNDLE-SCHEMA",  # or define EB-L0-REFS-MISSING
                message=f"Missing L0 refs (expected >=4 for chip/wiring/hardware/safety, got {len(verified.l0_refs)})",
                stage="validating",
            )
            events.append(_evt("validating", "failed", 0.2, {"l0_refs_count": len(verified.l0_refs)}))
            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="rejected",
                bundle_id=verified.bundle_id,
                bundle_hash=verified.bundle_hash,
                pulse_ir_hash=verified.pulse_ir.content_hash,
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        # 2. Simulate stages (MVP)
        events.append(_evt("preparing", "succeeded", 1.0))

        if request.mode == "dry_run":
            # Dry run: only validation, no actual execution, no L7 call, empty data
            events.append(_evt("uploading", "skipped", 2.0))
            events.append(_evt("arming", "skipped", 3.0))
            events.append(_evt("running", "skipped", 4.0))
            events.append(_evt("acquiring", "skipped", 5.0))
            events.append(_evt("completed", "succeeded", 6.0))

            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="succeeded",
                bundle_id=verified.bundle_id,
                bundle_hash=verified.bundle_hash,
                pulse_ir_hash=verified.pulse_ir.content_hash,
                result_level="integrated_iq",
                data={},
                events=tuple(events),
                diagnostics=(),
                metrics={"dry_run": True},
            )

        events.append(_evt("uploading", "skipped", 2.0))
        events.append(_evt("arming", "skipped", 3.0))
        events.append(_evt("running", "started", 4.0))

        # 3. Call the underlying virtual runner (L7) with typed request
        try:
            model_ref = TwinModelRef(
                model_id="trh.model.rabi_mvp",
                model_version="v0.1",
                model_kind="rabi_virtual_mvp",
                source="built_in",
            )
            cfg = VirtualQPUConfig(
                model_ref=model_ref,
                seed=42,
                noise_sigma=0.015,
                hidden_parameters={"pi_amp": 0.175},
            )
            trh_req = VirtualRunRequest(
                request_id=request.request_id,
                run_id=request.run_id,
                pulse_ir=verified.pulse_ir,
                config=cfg,
            )
            trh_res: VirtualRunResult = run_rabi_virtual_typed(trh_req)
            events.append(_evt("running", "succeeded", 10.0))
            events.append(_evt("acquiring", "succeeded", 11.0))
            events.append(_evt("completed", "succeeded", 12.0))
            iq_list = trh_res.data.get("iq", []) if isinstance(trh_res.data, dict) else []
            # Preserve TRH model lineage for audit (P1-004)
            trh_lineage = {
                "trh_result_schema": trh_res.schema_version,
                "model_id": trh_res.model_ref.model_id,
                "model_version": trh_res.model_ref.model_version,
                "seed": float(trh_res.seed),
                "noise_sigma": trh_res.metrics.get("noise_sigma", 0.0) if hasattr(trh_res, "metrics") else 0.0,
            }
        except Exception as e:
            diag = BackendDiagnostic(
                severity="error",
                code="EB-VIRTUAL-RUN-FAILED",
                message=f"L7 virtual run failed: {e}",
                stage="running",
            )
            events.append(_evt("running", "failed", 10.0, {"error": str(e)}))
            return BackendRunResult(
                run_id=request.run_id,
                backend_id=self.backend_id,
                final_state="failed",
                bundle_id=verified.bundle_id,
                bundle_hash=verified.bundle_hash,
                pulse_ir_hash=verified.pulse_ir.content_hash,
                result_level="integrated_iq",
                diagnostics=(diag,),
                events=tuple(events),
            )

        result = BackendRunResult(
            run_id=request.run_id,
            backend_id=self.backend_id,
            final_state="succeeded",
            bundle_id=verified.bundle_id,
            bundle_hash=verified.bundle_hash,
            pulse_ir_hash=verified.pulse_ir.content_hash,
            result_level="integrated_iq",
            data={"iq": iq_list, "trh_lineage": trh_lineage},
            events=tuple(events),
            diagnostics=(),
            metrics={
                "points": len(iq_list),
                "trh_seed": float(trh_res.seed),
            },
        )

        return result

    def cancel(self, run_id: str, reason: str) -> BackendRunResult:
        # MVP stub
        return BackendRunResult(
            run_id=run_id,
            backend_id=self.backend_id,
            final_state="cancelled",
            bundle_id="unknown",
            bundle_hash="",
            pulse_ir_hash="",
            result_level="integrated_iq",
            diagnostics=(BackendDiagnostic(severity="info", code="CANCELLED", message=reason),),
            events=(BackendEvent(
                event_id=str(uuid.uuid4()),
                run_id=run_id,
                backend_id=self.backend_id,
                stage="cancelled",
                state="succeeded",
                t_rel_ms=0.0,
                details={"reason": reason},
            ),),
        )

    def safe_stop(self, reason: str) -> BackendDiagnostic:
        return BackendDiagnostic(
            severity="info",
            code="SAFE_STOP",
            message=reason,
            stage="cleanup",
        )
