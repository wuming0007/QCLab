"""RuntimeService MVP implementation per QXtrl_L4_RS_RuntimeScheduler_设计.md.

Single-process, synchronous run_once for Rabi virtual.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from qxtrl.el.models import ExperimentSpec
from qxtrl.cpir import compile_to_bundle
from qxtrl.eb import VirtualExecutionBackend
from qxtrl.eb.models import BackendSubmitRequest
from qxtrl.co import analyze_rabi
from qxtrl.ds import record_runtime_result  # legacy record_run kept only for compat in manifest.py

from .models import (
    RunRequest,
    RunReceipt,
    RunState,
    RunEvent,
    RuntimeDiagnostic,
    StageTiming,
    RuntimeRunResult,
)


class InMemoryEventStore:
    """MVP in-memory event store for runs."""

    def __init__(self):
        self._events: dict[str, list[RunEvent]] = {}
        self._states: dict[str, RunState] = {}

    def append_event(self, event: RunEvent):
        self._events.setdefault(event.run_id, []).append(event)

    def list_events(self, run_id: str) -> tuple[RunEvent, ...]:
        return tuple(self._events.get(run_id, []))

    def update_state(self, state: RunState):
        self._states[state.run_id] = state

    def get_state(self, run_id: str) -> RunState | None:
        return self._states.get(run_id)

    def get_last_event_id(self, run_id: str) -> str | None:
        evs = self._events.get(run_id, [])
        return evs[-1].event_id if evs else None


class InMemoryResourceLockManager:
    """MVP global lock manager. For real, would use line-based or L0 groups."""

    def __init__(self):
        self._held: dict[str, str] = {}  # key -> run_id

    def acquire(self, run_id: str, keys: tuple[str, ...], timeout_s: float = 10.0) -> bool:
        # MVP: simple exclusive on any key
        start = time.time()
        while time.time() - start < timeout_s:
            conflict = False
            for k in keys:
                if k in self._held and self._held[k] != run_id:
                    conflict = True
                    break
            if not conflict:
                for k in keys:
                    self._held[k] = run_id
                return True
            time.sleep(0.01)
        return False

    def release(self, run_id: str, keys: tuple[str, ...]):
        for k in keys:
            if self._held.get(k) == run_id:
                del self._held[k]


class RuntimeService:
    """MVP Runtime & Scheduler.

    Provides run_once() that orchestrates the full chain without bypassing layers.
    """

    def __init__(self, backend: Optional[VirtualExecutionBackend] = None, result_base_dir: str = "runs"):
        self._backend = backend or VirtualExecutionBackend()
        self._lock_manager = InMemoryResourceLockManager()
        self._event_store = InMemoryEventStore()
        self._result_base_dir = result_base_dir

    def _now_ns(self) -> int:
        return time.time_ns()

    def _emit_event(
        self,
        run_id: str,
        request_id: str,
        stage: str,
        state: str,
        code: str,
        message: str,
        t_rel_ms: float,
        severity: str = "info",
        source_layer: str = "rs",
        payload: Optional[dict[str, Any]] = None,
    ) -> RunEvent:
        evt = RunEvent(
            event_id=str(uuid.uuid4()),
            run_id=run_id,
            request_id=request_id,
            source_layer=source_layer,  # type: ignore
            stage=stage,  # type: ignore
            state=state,  # type: ignore
            severity=severity,  # type: ignore
            code=code,
            message=message,
            t_rel_ms=t_rel_ms,
            payload=payload or {},
        )
        self._event_store.append_event(evt)
        return evt

    def _record_timing(self, run_id: str, stage: str, start_ns: int, end_ns: int, status: str) -> StageTiming:
        dur = (end_ns - start_ns) / 1e6
        timing = StageTiming(
            run_id=run_id,
            stage=stage,
            started_at_ns=start_ns,
            ended_at_ns=end_ns,
            duration_ms=dur,
            status=status,  # type: ignore
        )
        # Could store timings too, but for MVP attach to result
        return timing

    def _persist_l5(self, result: "RuntimeRunResult", spec: Any = None, bundle: Any = None) -> Optional[str]:
        """Best effort persist to L5. Early failures also produce manifests."""
        try:
            return record_runtime_result(runtime_result=result, spec=spec, bundle=bundle, base_dir=self._result_base_dir)
        except Exception:
            return None

    def _finalize(
        self,
        run_id: str,
        request_id: str,
        final_state: str,
        diagnostics: list[RuntimeDiagnostic],
        events: list[RunEvent],
        timings: list[StageTiming],
        t0: int,
        **extra: Any,
    ) -> RuntimeRunResult:
        """Unified finalizer for ALL paths (early returns + main) to guarantee:
        - total timing
        - terminal RS-FAILED / RS-COMPLETED event
        - metrics.total_duration_ms
        - RunState written (for get_state visibility on early failures)
        """
        total_end = self._now_ns()
        dur = (total_end - t0) / 1e6

        if not any(getattr(t, "stage", None) == "total" for t in timings):
            tstatus = "succeeded" if final_state == "succeeded" else ("skipped" if final_state == "cancelled" else "failed")
            timings.append(self._record_timing(run_id, "total", t0, total_end, tstatus))

        has_terminal = any(e.code in ("RS-COMPLETED", "RS-FAILED") for e in events)
        if not has_terminal:
            if final_state == "succeeded":
                te = self._emit_event(run_id, request_id, "completed", "succeeded", "RS-COMPLETED", "run completed", dur, "info")
            else:
                te = self._emit_event(run_id, request_id, "failed", "failed", "RS-FAILED", f"run {final_state}", dur, "error")
            events.append(te)

        metrics = {"total_duration_ms": dur}
        # merge any caller metrics
        m = extra.pop("metrics", None)
        if isinstance(m, dict):
            metrics.update(m)

        res = RuntimeRunResult(
            run_id=run_id,
            request_id=request_id,
            final_state=final_state,  # type: ignore
            events=tuple(events),
            diagnostics=tuple(diagnostics),
            timings=tuple(timings),
            metrics=metrics,
            **{k: v for k, v in extra.items() if v is not None},
        )

        # Always write state so get_state() sees early failures too
        ls = final_state if final_state in ("succeeded", "failed", "cancelled", "rejected") else "succeeded"
        self._event_store.update_state(RunState(
            run_id=run_id,
            request_id=request_id,
            lifecycle_state=ls,  # type: ignore
            backend_id=extra.get("backend_id"),
            mode=extra.get("mode", "virtual"),
            current_stage="completed" if final_state == "succeeded" else final_state,
            last_event_id=events[-1].event_id if events else None,
            diagnostics=tuple(diagnostics),
        ))
        return res

    def submit(self, request: RunRequest | dict[str, Any]) -> RunReceipt:
        """MVP admission-only submit.

        Performs request validation + mode gate, returns RunReceipt (accepted or rejected).
        Does NOT execute the experiment or compile.
        The full execution entry point is run_once().

        L4 v0.1 is synchronous; async queue/worker semantics are future (v0.2+).
        See design doc §5 for submit vs run_once contract.
        """
        t0 = self._now_ns()
        try:
            if isinstance(request, dict):
                request = RunRequest.model_validate(request)
            run_id = request.run_id or f"run.{request.request_id}.{uuid.uuid4().hex[:8]}"
            # Basic admission
            if request.mode not in ("dry_run", "virtual"):
                diag = RuntimeDiagnostic(severity="error", code="RS-UNSUPPORTED-MODE", message=f"mode {request.mode} not allowed in MVP")
                self._emit_event(run_id, request.request_id, "admission", "failed", "RS-UNSUPPORTED-MODE", str(diag.message), 0.0, "error")
                return RunReceipt(
                    request_id=request.request_id,
                    run_id=run_id,
                    accepted=False,
                    state="rejected",
                    submitted_at_ns=t0,
                    diagnostics=(diag,),
                )
            receipt = RunReceipt(
                request_id=request.request_id,
                run_id=run_id,
                accepted=True,
                state="accepted",
                submitted_at_ns=t0,
            )
            self._emit_event(run_id, request.request_id, "admission", "succeeded", "RS-ADMISSION", "request accepted", 0.0)
            # seed state so get_state/cancel can see it pre-run_once
            self._event_store.update_state(RunState(
                run_id=run_id,
                request_id=request.request_id,
                lifecycle_state="accepted",
                backend_id=request.backend_id,
                mode=request.mode,
                current_stage="accepted",
                last_event_id=None,
                diagnostics=(),
            ))
            return receipt
        except Exception as e:
            run_id = getattr(request, "run_id", None) or f"run.err.{uuid.uuid4().hex[:8]}"
            req_id = getattr(request, "request_id", "unknown")
            self._emit_event(run_id, req_id, "admission", "failed", "RS-REQUEST-SCHEMA", str(e), 0.0, "error")
            return RunReceipt(
                request_id=req_id,
                run_id=run_id,
                accepted=False,
                state="rejected",
                submitted_at_ns=t0,
                diagnostics=(RuntimeDiagnostic(severity="error", code="RS-REQUEST-SCHEMA", message=str(e)),),
            )

    def get_state(self, run_id: str) -> RunState | None:
        return self._event_store.get_state(run_id)

    def list_events(self, run_id: str) -> tuple[RunEvent, ...]:
        return self._event_store.list_events(run_id)

    def cancel(self, run_id: str, reason: str, requested_by: str | None = None) -> RuntimeRunResult:
        """MVP cancel: best-effort. Cannot interrupt in-flight sync run_once().
        If run unknown or already terminal, returns appropriate diagnostic.
        """
        existing = self._event_store.get_state(run_id)
        req_id = existing.request_id if existing else "unknown"
        if not existing:
            diag = RuntimeDiagnostic(severity="error", code="RS-CANCEL-UNKNOWN", message=f"run {run_id} not known", stage="cancelled")
            evt = self._emit_event(run_id, req_id, "cancelled", "failed", "RS-CANCEL-UNKNOWN", reason, 0.0, "error")
            return RuntimeRunResult(
                run_id=run_id, request_id=req_id, final_state="rejected",
                diagnostics=(diag,), events=(evt,), timings=(),
            )
        if existing.lifecycle_state in ("succeeded", "failed", "cancelled", "rejected"):
            diag = RuntimeDiagnostic(severity="info", code="RS-CANCEL-IGNORED", message="run already terminal", stage="cancelled")
            evt = self._emit_event(run_id, req_id, "cancelled", "info", "RS-CANCEL-IGNORED", reason, 0.0, "info")
            return RuntimeRunResult(
                run_id=run_id, request_id=req_id, final_state=existing.lifecycle_state,  # type: ignore
                diagnostics=(diag,), events=(evt, *self._event_store.list_events(run_id)[-3:]), timings=(),
            )
        # otherwise mark cancelled (note: if currently inside run_once, this will not stop it)
        diag = RuntimeDiagnostic(severity="warning", code="RS-CANCELLED", message=reason, stage="cancelled", source_layer="rs")
        evt = self._emit_event(run_id, req_id, "cancelled", "succeeded", "RS-CANCELLED", reason, 0.0, "warning")
        res = RuntimeRunResult(
            run_id=run_id, request_id=req_id, final_state="cancelled",
            diagnostics=(diag,), events=(evt,), timings=(),
        )
        self._event_store.update_state(RunState(
            run_id=run_id, request_id=req_id, lifecycle_state="cancelled",
            backend_id=existing.backend_id, mode=existing.mode,
            current_stage="cancelled", last_event_id=evt.event_id,
            diagnostics=(diag,),
        ))
        return res

    def run_once(self, request: RunRequest | dict[str, Any]) -> RuntimeRunResult:
        """Main MVP execution entry: synchronous full lifecycle (validate L1 -> L2 compile -> resource -> L3 -> L6 -> L5).

        All paths (success and early failure) produce uniform RuntimeRunResult with:
        - total timing + terminal event (RS-COMPLETED / RS-FAILED)
        - metrics.total_duration_ms
        - RunState written for get_state() visibility
        """

        timings: list[StageTiming] = []
        diagnostics: list[RuntimeDiagnostic] = []
        events: list[RunEvent] = []
        t0 = self._now_ns()

        # 1. Validate request
        t_start = self._now_ns()
        try:
            if isinstance(request, dict):
                request = RunRequest.model_validate(request)
            # assign run_id early for admission failures to be traceable
            if not getattr(request, "run_id", None):
                tentative_run_id = f"run.{request.request_id}.{uuid.uuid4().hex[:8]}"
                request = request.model_copy(update={"run_id": tentative_run_id})
            run_id = request.run_id
            if request.mode not in ("dry_run", "virtual"):
                diag = RuntimeDiagnostic(severity="error", code="RS-UNSUPPORTED-MODE", message=f"mode {request.mode} not allowed in MVP")
                diagnostics.append(diag)
                evt = self._emit_event(run_id, request.request_id, "admission", "failed", "RS-UNSUPPORTED-MODE", str(diag.message), 0.0, "error")
                events.append(evt)
                timings.append(self._record_timing(run_id, "validate_request", t_start, self._now_ns(), "failed"))
                res = self._finalize(
                    run_id, request.request_id, "rejected", diagnostics, events, timings, t0,
                    mode=request.mode,
                )
                mref = self._persist_l5(res, spec=getattr(request, 'experiment_spec', None))
                if mref:
                    try:
                        res = res.model_copy(update={"manifest_ref": mref})
                    except Exception:
                        pass
                return res
        except Exception as e:
            run_id = getattr(request, "run_id", None) or f"run.err.{uuid.uuid4().hex[:8]}"
            req_id = getattr(request, "request_id", "unknown")
            diag = RuntimeDiagnostic(severity="error", code="RS-REQUEST-SCHEMA", message=str(e), stage="admission")
            diagnostics.append(diag)
            evt = self._emit_event(run_id, req_id, "admission", "failed", "RS-REQUEST-SCHEMA", str(e), 0.0, "error")
            events.append(evt)
            timings.append(self._record_timing(run_id, "validate_request", t_start, self._now_ns(), "failed"))
            res = self._finalize(
                run_id, req_id, "rejected", diagnostics, events, timings, t0,
            )
            mref = self._persist_l5(res, spec=getattr(request, 'experiment_spec', None))
            if mref:
                try:
                    res = res.model_copy(update={"manifest_ref": mref})
                except Exception:
                    pass
            return res
        timings.append(self._record_timing(run_id, "validate_request", t_start, self._now_ns(), "succeeded"))
        events.append(self._emit_event(run_id, request.request_id, "admission", "succeeded", "RS-ADMISSION", "request accepted", 0.0))

        # 2. Validate L1 spec
        t_start = self._now_ns()
        try:
            if isinstance(request.experiment_spec, dict):
                spec = ExperimentSpec.model_validate(request.experiment_spec)
            else:
                spec = request.experiment_spec
            # re-validate for safety
            spec = ExperimentSpec.model_validate(spec.model_dump(mode="python"))
        except Exception as e:
            diag = RuntimeDiagnostic(severity="error", code="RS-REQUEST-SCHEMA", message=f"L1 validation failed: {e}", stage="validating")
            diagnostics.append(diag)
            events.append(self._emit_event(run_id, request.request_id, "validating", "failed", "RS-REQUEST-SCHEMA", str(e), (self._now_ns()-t0)/1e6, "error"))
            timings.append(self._record_timing(run_id, "validate_l1", t_start, self._now_ns(), "failed"))
            res = self._finalize(run_id, request.request_id, "rejected", diagnostics, events, timings, t0)
            mref = self._persist_l5(res, spec=request.experiment_spec)
            if mref:
                try:
                    res = res.model_copy(update={"manifest_ref": mref})
                except Exception:
                    pass
            return res

        timings.append(self._record_timing(run_id, "validate_l1", t_start, self._now_ns(), "succeeded"))
        events.append(self._emit_event(run_id, request.request_id, "validating", "succeeded", "RS-VALIDATE-L1", "L1 spec valid", (self._now_ns()-t0)/1e6 ))

        # 3. Compile via L2
        t_start = self._now_ns()
        try:
            bundle = compile_to_bundle(spec)
            events.append(self._emit_event(run_id, request.request_id, "compiling", "succeeded", "RS-COMPILE", "L2 compile ok", (self._now_ns()-t0)/1e6, payload={"bundle_id": bundle.bundle_id}))
        except Exception as e:
            diag = RuntimeDiagnostic(severity="error", code="RS-COMPILE-FAILED", message=str(e), stage="compiling")
            diagnostics.append(diag)
            events.append(self._emit_event(run_id, request.request_id, "compiling", "failed", "RS-COMPILE-FAILED", str(e), (self._now_ns()-t0)/1e6, "error"))
            timings.append(self._record_timing(run_id, "compile_l2", t_start, self._now_ns(), "failed"))
            res = self._finalize(run_id, request.request_id, "failed", diagnostics, events, timings, t0)
            mref = self._persist_l5(res, spec=spec, bundle=None)  # bundle not available on compile fail
            if mref:
                try:
                    res = res.model_copy(update={"manifest_ref": mref})
                except Exception:
                    pass
            return res
        timings.append(self._record_timing(run_id, "compile_l2", t_start, self._now_ns(), "succeeded"))

        # 4. Acquire resources (MVP global)
        t_start = self._now_ns()
        resource_keys = ("resource.global.default",)  # MVP simple
        if hasattr(bundle.pulse_ir, "resources") and bundle.pulse_ir.resources.line_ids:
            resource_keys += tuple(f"line:{lid}" for lid in bundle.pulse_ir.resources.line_ids)
        acquired = self._lock_manager.acquire(run_id, resource_keys, timeout_s=request.timeout_s)
        if not acquired:
            diag = RuntimeDiagnostic(severity="error", code="RS-RESOURCE-BUSY", message="failed to acquire resources", stage="waiting_for_resources")
            diagnostics.append(diag)
            events.append(self._emit_event(run_id, request.request_id, "waiting_for_resources", "failed", "RS-RESOURCE-BUSY", "lock timeout", (self._now_ns()-t0)/1e6, "error"))
            timings.append(self._record_timing(run_id, "acquire_resources", t_start, self._now_ns(), "failed"))
            res = self._finalize(run_id, request.request_id, "rejected", diagnostics, events, timings, t0)
            mref = self._persist_l5(res, spec=spec, bundle=bundle)
            if mref:
                try:
                    res = res.model_copy(update={"manifest_ref": mref})
                except Exception:
                    pass
            return res
        events.append(self._emit_event(run_id, request.request_id, "resources_acquired", "succeeded", "RS-RESOURCE", "resources acquired", (self._now_ns()-t0)/1e6 ))
        timings.append(self._record_timing(run_id, "acquire_resources", t_start, self._now_ns(), "succeeded"))

        try:
            # 5. Submit to L3
            t_start = self._now_ns()
            be_req = BackendSubmitRequest(
                request_id=request.request_id,
                run_id=run_id,
                backend_id=request.backend_id,
                bundle=bundle,
                mode=request.mode,
            )
            backend_result = self._backend.submit(be_req)
            be_succ = backend_result.final_state == "succeeded"
            backend_sev = "info" if be_succ else "error"
            events.append(self._emit_event(
                run_id, request.request_id, "backend_submit",
                "succeeded" if be_succ else "failed",
                "RS-BACKEND", f"backend {backend_result.final_state}",
                (self._now_ns()-t0)/1e6, backend_sev
            ))
            timings.append(self._record_timing(run_id, "submit_l3", t_start, self._now_ns(), "succeeded" if be_succ else "failed"))

            # Map L3 BackendDiagnostic -> RuntimeDiagnostic (source_layer eb) + RS summary codes
            if not be_succ:
                rs_code = "RS-BACKEND-REJECTED" if backend_result.final_state == "rejected" else "RS-BACKEND-FAILED"
                rs_diag = RuntimeDiagnostic(
                    severity="error",
                    code=rs_code,
                    message=f"backend returned {backend_result.final_state}",
                    stage="backend_submit",
                    source_layer="rs",
                )
                # avoid duplicate if already present
                if not any(d.code == rs_code for d in diagnostics):
                    diagnostics.append(rs_diag)
                for bd in backend_result.diagnostics:
                    diagnostics.append(RuntimeDiagnostic(
                        severity=bd.severity,
                        code=bd.code,
                        message=bd.message,
                        stage=bd.stage,
                        source_layer="eb",
                        path=bd.path,
                        hint=bd.hint,
                    ))

            # 6. Analyze via L6 (if not dry_run failure)
            analysis_result = None
            t_start = self._now_ns()
            if be_succ and request.mode != "dry_run":
                try:
                    l6_input = {"result": backend_result.data.get("iq", []), "backend": request.backend_id}
                    analysis_result = analyze_rabi(l6_input)
                    events.append(self._emit_event(run_id, request.request_id, "analyzing", "succeeded", "RS-ANALYZE", "L6 analysis ok", (self._now_ns()-t0)/1e6))
                    timings.append(self._record_timing(run_id, "analyze_l6", t_start, self._now_ns(), "succeeded"))
                except Exception as e:
                    diag = RuntimeDiagnostic(severity="error", code="RS-ANALYSIS-FAILED", message=str(e), stage="analyzing")
                    diagnostics.append(diag)
                    events.append(self._emit_event(run_id, request.request_id, "analyzing", "failed", "RS-ANALYSIS-FAILED", str(e), (self._now_ns()-t0)/1e6, "error"))
                    timings.append(self._record_timing(run_id, "analyze_l6", t_start, self._now_ns(), "failed"))
                    # continue to persist what we have
            else:
                timings.append(self._record_timing(run_id, "analyze_l6", t_start, self._now_ns(), "skipped"))

            # 7. Persist via L5: append persist timing/event, build COMPLETE res via _finalize, then single-track new record_runtime_result (L5 receives full incl terminal/total)
            final_state = backend_result.final_state if not be_succ else ("failed" if diagnostics else "succeeded")
            manifest_ref = None
            t_start = self._now_ns()
            try:
                persist_code = "RS-PERSIST" if final_state == "succeeded" and not diagnostics else "RS-PERSIST-RECORD"
                persist_msg = "L5 record ok" if persist_code == "RS-PERSIST" else f"L5 record for backend {backend_result.final_state}"
                events.append(self._emit_event(run_id, request.request_id, "persisting", "succeeded", persist_code, persist_msg, (self._now_ns()-t0)/1e6, "info" if final_state == "succeeded" else "warning"))
                timings.append(self._record_timing(run_id, "persist_l5", t_start, self._now_ns(), "succeeded"))
            except Exception as e:
                diag = RuntimeDiagnostic(severity="error", code="RS-PERSIST-FAILED", message=str(e), stage="persisting")
                diagnostics.append(diag)
                timings.append(self._record_timing(run_id, "persist_l5", t_start, self._now_ns(), "failed"))
                manifest_ref = None

            # Build COMPLETE result now (includes the persist timing/event + total + terminal)
            res = self._finalize(
                run_id, request.request_id, final_state, diagnostics, events, timings, t0,
                l1_spec_id=spec.spec_id,
                bundle_id=backend_result.bundle_id,
                backend_id=request.backend_id,
                backend_result=backend_result,
                analysis_result=analysis_result,
                manifest_ref=manifest_ref,
                mode=request.mode,
            )

            # Call new L5 with the complete res (L5 gets terminal, total, persist etc.)
            if manifest_ref is None:
                try:
                    manifest_ref = record_runtime_result(runtime_result=res, spec=spec, bundle=bundle, base_dir=self._result_base_dir)
                    try:
                        res = res.model_copy(update={"manifest_ref": manifest_ref})
                    except Exception:
                        pass
                except Exception:
                    # best-effort; surface via diagnostics in caller if needed
                    # (previous versions added RS-PERSIST-FAILED before finalizing res)
                    pass

            return res

        finally:
            # Always release resources
            self._lock_manager.release(run_id, resource_keys)
