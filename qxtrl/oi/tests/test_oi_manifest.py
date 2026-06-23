"""Manifest view tests."""

import tempfile

from qxtrl.oi import show_manifest
from qxtrl.oi.manifest import parse_run_id
from qxtrl.rs import RuntimeService, RunRequest
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cc import minimal_rabi_lab


def test_parse_run_id():
    assert parse_run_id("run.foo.bar") == "run.foo.bar"
    assert "run" in parse_run_id("qxtrl://runs/run.foo.bar/manifest.json")


def test_parse_run_id_rejects_bad_refs():
    bads = [
        "qxtrl://evil/run.foo/notmanifest.json",
        "qxtrl://runs/../manifest.json",
        "qxtrl://runs/bad/../seg/manifest.json",
    ]
    for b in bads:
        try:
            parse_run_id(b)
            assert False, f"should reject {b}"
        except Exception:
            pass  # expected


def test_cli_manifest_show_reads_resultstore():
    lab = minimal_rabi_lab()
    spec = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=lab["chip"],
        l0_wiring_ref=lab["wiring"],
        l0_hw_ref=lab["hardware"],
        l0_safety_ref=lab["safety"],
    )
    runtime = RuntimeService()
    req = RunRequest(request_id="oi-manifest-test", experiment_spec=spec)
    res = runtime.run_once(req)

    with tempfile.TemporaryDirectory() as tmp:
        # force manifest into tmp
        from qxtrl.ds import FileResultStore
        st = FileResultStore(base_dir=tmp)
        st.record_runtime_result(runtime_result=res, spec=spec)

        view = show_manifest(res.run_id, result_dir=tmp)
        assert view.run_id == res.run_id
        assert view.final_state == "succeeded"


def test_manifest_missing_raises():
    try:
        show_manifest("run.does.not.exist.123456")
        assert False, "should raise for missing"
    except Exception as e:
        assert "no manifest" in str(e).lower() or "not found" in str(e).lower()
