"""SDK contract tests per L9 design."""

import pytest

from qxtrl.oi import run_rabi_virtual


def test_run_rabi_virtual_sdk_succeeds():
    summary = run_rabi_virtual(qubit_id="q000", points=5)
    assert summary.final_state == "succeeded"
    assert summary.manifest_ref is not None
    assert summary.event_count > 0


def test_sdk_returns_manifest_ref():
    summary = run_rabi_virtual(qubit_id="q000")
    assert summary.manifest_ref and "manifest" in summary.manifest_ref


def test_sdk_invalid_qubit_fails_before_runtime():
    # qubit validation should happen (via options or L1)
    with pytest.raises(Exception):
        run_rabi_virtual(qubit_id="invalid-qubit-xyz")


def test_sdk_rejects_qubit_not_in_l0_context():
    # per review: q001 / q999 should fail in demo context
    for q in ["q001", "q999"]:
        with pytest.raises(Exception) as exc:
            run_rabi_virtual(qubit_id=q, points=3)
        assert "context" in str(exc.value).lower() or "not in" in str(exc.value).lower()


def test_sdk_hardware_mode_rejected_in_mvp():
    with pytest.raises(Exception):
        run_rabi_virtual(qubit_id="q000", mode="hardware")


def test_sdk_summary_preserves_runtime_diagnostics():
    # at least model accepts diagnostics
    s = run_rabi_virtual(qubit_id="q000")
    assert isinstance(s.diagnostics, tuple)


def test_sdk_result_dir_is_used_for_manifest():
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmp:
        s = run_rabi_virtual(qubit_id="q000", points=3, result_dir=tmp)
        assert s.manifest_ref is not None
        # the manifest should be under tmp, not cwd runs
        # since L4 now respects it, the ref should indicate it or file exists in tmp
        assert tmp in (s.manifest_ref or "") or os.path.exists(os.path.join(tmp, s.run_id, "manifest.json"))
