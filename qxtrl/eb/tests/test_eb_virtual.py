"""Key contract tests for L3/EB as per Jed review and design doc."""

import pytest

from qxtrl.eb import VirtualExecutionBackend
from qxtrl.eb.models import BackendSubmitRequest
from qxtrl.cpir import compile_to_bundle
from qxtrl.cpir.compiler import _recompute_pulse_ir_content_hash, _recompute_bundle_hash
from qxtrl.cpir.pulse_ir import PulseIR, CompiledBundle
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cc import minimal_rabi_lab


@pytest.fixture
def good_bundle():
    lab = minimal_rabi_lab()
    spec = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=lab["chip"],
        l0_wiring_ref=lab["wiring"],
        l0_hw_ref=lab["hardware"],
        l0_safety_ref=lab["safety"],
    )
    return compile_to_bundle(spec)


@pytest.fixture
def backend():
    return VirtualExecutionBackend()


def test_virtual_backend_accepts_valid_rabi_bundle(backend, good_bundle):
    req = BackendSubmitRequest(
        request_id="r1", run_id="run1", backend_id=backend.backend_id, bundle=good_bundle
    )
    result = backend.submit(req)
    assert result.final_state == "succeeded"
    assert len(result.data.get("iq", [])) > 0


def test_backend_rejects_wrong_backend_id(backend, good_bundle):
    req = BackendSubmitRequest(
        request_id="r1", run_id="run1", backend_id="backend.wrong", bundle=good_bundle
    )
    result = backend.submit(req)
    assert result.final_state == "rejected"
    assert any(d.code == "EB-UNSUPPORTED-BACKEND" for d in result.diagnostics)


def test_backend_rejects_missing_l0_refs(backend, good_bundle):
    """Forge a hash-valid bundle with l0_refs=() and assert L3 rejects it."""
    bundle_dict = good_bundle.model_dump()

    # Tamper l0_refs
    bundle_dict['l0_refs'] = ()

    # Recompute bundle hash (l0 change doesn't affect pir hash)
    temp_for_hash = CompiledBundle.model_validate(bundle_dict)
    bundle_dict['bundle_hash'] = _recompute_bundle_hash(temp_for_hash)

    tampered = CompiledBundle.model_validate(bundle_dict)

    req = BackendSubmitRequest(
        request_id="r1", run_id="run1", backend_id=backend.backend_id, bundle=tampered
    )
    result = backend.submit(req)
    assert result.final_state == "rejected"
    assert any("L0" in d.message or "l0" in d.message.lower() or d.code in ("EB-BUNDLE-SCHEMA", "EB-BUNDLE-VERIFY") for d in result.diagnostics)


def test_backend_rejects_unsupported_result_level(backend, good_bundle):
    """Forge a hash-valid bundle with unsupported result_level (e.g. raw_iq) and assert rejection."""
    bundle_dict = good_bundle.model_dump()

    # Tamper result_level in acquisition_windows
    acq_wins = bundle_dict['pulse_ir'].get('acquisition_windows', [])
    if acq_wins:
        acq_wins[0]['result_level'] = 'raw_iq'

    # Recompute pir hash
    temp_pir = PulseIR.model_validate(bundle_dict['pulse_ir'])
    bundle_dict['pulse_ir']['content_hash'] = _recompute_pulse_ir_content_hash(temp_pir)

    # Recompute bundle hash
    temp_bundle = CompiledBundle.model_validate(bundle_dict)
    bundle_dict['bundle_hash'] = _recompute_bundle_hash(temp_bundle)

    tampered = CompiledBundle.model_validate(bundle_dict)

    req = BackendSubmitRequest(
        request_id="r1", run_id="run1", backend_id=backend.backend_id, bundle=tampered
    )
    result = backend.submit(req)
    assert result.final_state == "rejected"
    assert any(d.code == "EB-UNSUPPORTED-RESULT-LEVEL" for d in result.diagnostics)


def test_backend_rejects_raw_pulseir_input_as_result_not_exception(backend):
    lab = minimal_rabi_lab()
    spec = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=lab["chip"],
        l0_wiring_ref=lab["wiring"],
        l0_hw_ref=lab["hardware"],
        l0_safety_ref=lab["safety"],
    )
    from qxtrl.cpir import compile_experiment_spec
    raw_ir = compile_experiment_spec(spec)
    bad = {"request_id": "r", "run_id": "run", "backend_id": backend.backend_id, "bundle": raw_ir}
    result = backend.submit(bad)
    assert result.final_state == "rejected"
    assert any("SCHEMA" in d.code or "VERIFY" in d.code for d in result.diagnostics)


def test_backend_runtime_failure_returns_failed_result(backend, good_bundle, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("sim l7")
    monkeypatch.setattr("qxtrl.eb.virtual.run_rabi_virtual_typed", boom)
    req = BackendSubmitRequest(
        request_id="r1", run_id="run1", backend_id=backend.backend_id, bundle=good_bundle
    )
    result = backend.submit(req)
    assert result.final_state == "failed"
    assert any(d.code == "EB-VIRTUAL-RUN-FAILED" for d in result.diagnostics)


def test_dry_run_does_not_execute_l7(backend, good_bundle):
    req = BackendSubmitRequest(
        request_id="r1", run_id="run1", backend_id=backend.backend_id, bundle=good_bundle, mode="dry_run"
    )
    result = backend.submit(req)
    assert result.final_state == "succeeded"
    assert result.data == {} or not result.data.get("iq")
    assert any(getattr(e, "state", None) == "skipped" for e in result.events if getattr(e, "stage", None) in ("running", "acquiring"))
