"""Tests for L7 / TRH per design: typed, deterministic, replay inspect."""

import subprocess
import sys

from qxtrl.trh import run_rabi_virtual, run_rabi_virtual_typed
from qxtrl.trh.models import (
    TwinModelRef,
    VirtualQPUConfig,
    VirtualRunRequest,
    VirtualRunResult,
)
from qxtrl.cpir import compile_experiment_spec
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cc import minimal_rabi_lab
from qxtrl.trh.replay import build_replay_plan, replay_manifest
from qxtrl.trh.models import ReplayRequest


def test_run_rabi_virtual_from_ir():
    lab = minimal_rabi_lab()
    spec = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=lab["chip"],
        l0_wiring_ref=lab["wiring"],
        l0_hw_ref=lab["hardware"],
        l0_safety_ref=lab["safety"],
    )
    ir = compile_experiment_spec(spec)
    res = run_rabi_virtual(ir, noise=0.01)
    assert "result" in res
    assert isinstance(res["result"], list)
    assert len(res["result"]) == 5
    assert res.get("backend") == "virtual_mvp"
    is_ = [p["i"] for p in res["result"]]
    assert max(is_) - min(is_) > 0.5


def test_virtual_rabi_typed_and_deterministic():
    lab = minimal_rabi_lab()
    spec = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=lab["chip"],
        l0_wiring_ref=lab["wiring"],
        l0_hw_ref=lab["hardware"],
        l0_safety_ref=lab["safety"],
    )
    ir = compile_experiment_spec(spec)

    model_ref = TwinModelRef(
        model_id="trh.model.rabi_mvp", model_version="v0.1", model_kind="rabi_virtual_mvp"
    )
    cfg = VirtualQPUConfig(model_ref=model_ref, seed=123, noise_sigma=0.01)
    req = VirtualRunRequest(request_id="r1", run_id="run1", pulse_ir=ir, config=cfg)

    res1 = run_rabi_virtual_typed(req)
    res2 = run_rabi_virtual_typed(req)
    assert isinstance(res1, VirtualRunResult)
    assert res1.final_state == "succeeded"
    assert res1.seed == 123
    assert res1.model_ref.model_id == "trh.model.rabi_mvp"
    # deterministic
    assert res1.data == res2.data


def test_virtual_determinism_cross_process():
    # simple subprocess check for cross process (avoids hash drift)
    code = '''
from qxtrl.trh import run_rabi_virtual_typed
from qxtrl.trh.models import TwinModelRef, VirtualQPUConfig, VirtualRunRequest
from qxtrl.cpir import compile_experiment_spec
from qxtrl.el import create_rabi_experiment_spec
from qxtrl.cc import minimal_rabi_lab
lab = minimal_rabi_lab()
spec = create_rabi_experiment_spec(qubit_id="q000", l0_chip_model_ref=lab["chip"], l0_wiring_ref=lab["wiring"], l0_hw_ref=lab["hardware"], l0_safety_ref=lab["safety"])
ir = compile_experiment_spec(spec)
model_ref = TwinModelRef(model_id="trh.model.rabi_mvp", model_version="v0.1", model_kind="rabi_virtual_mvp")
cfg = VirtualQPUConfig(model_ref=model_ref, seed=99, noise_sigma=0.01)
req = VirtualRunRequest(request_id="r", run_id="r", pulse_ir=ir, config=cfg)
res = run_rabi_virtual_typed(req)
print(res.data["iq"][0]["i"])
'''
    out1 = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    out2 = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    assert out1 == out2


def test_replay_inspect_from_manifest(tmp_path):
    # minimal: use a mock manifest via L5, but for test use direct
    # For simplicity, test plan build with bad ref
    req = ReplayRequest(replay_id="rp1", run_id_or_manifest_ref="run.does.not.exist", result_dir=str(tmp_path))
    plan = build_replay_plan(req)
    assert any(d.code == "TRH-MANIFEST-NOT-FOUND" for d in plan.diagnostics)

    res = replay_manifest(req)
    assert res.final_state in ("rejected", "failed")


def test_virtual_config_rejects_bool_nan_inf_negative():
    model_ref = TwinModelRef(model_id="t", model_version="v0.1", model_kind="rabi_virtual_mvp")
    from pydantic import ValidationError
    bad_cases = [
        {"seed": True},
        {"noise_sigma": True},
        {"noise_sigma": float("nan")},
        {"noise_sigma": float("inf")},
        {"noise_sigma": -0.1},
        {"hidden_parameters": {"pi_amp": float("nan")}},
    ]
    for case in bad_cases:
        cfg = {"model_ref": model_ref, **case}
        try:
            VirtualQPUConfig(**cfg)
            assert False, f"should reject {case}"
        except ValidationError:
            pass


def test_virtual_result_data_rejects_nan_inf():
    from pydantic import ValidationError
    model_ref = TwinModelRef(model_id="t", model_version="v0.1", model_kind="rabi_virtual_mvp")
    bad_data = {"iq": [{"amp": 0.0, "i": float("nan"), "q": 0.0}]}
    try:
        VirtualRunResult(
            run_id="r", final_state="succeeded", model_ref=model_ref, seed=1, result_level="iq", data=bad_data
        )
        assert False
    except ValidationError:
        pass


def test_replay_inspect_uses_manifest_experiment_and_compile_fields():
    # Use real L5 manifest structure
    import tempfile
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef, DatasetRef
    from qxtrl.trh.models import ReplayRequest
    with tempfile.TemporaryDirectory() as tmp:
        store = FileResultStore(base_dir=tmp)
        # create a minimal valid manifest in L5 structure
        dsref = DatasetRef(dataset_id="d1", run_id="run1", logical_uri="qxtrl://runs/run1/raw/iq.json", content_hash="sha256:0000000000000000", metadata_hash="sha256:1111111111111111")
        m = RunManifest(
            run_id="run1",
            final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="exp1", schema_version="v1"),
            compile=CompileManifestRef(bundle_id="b1", bundle_hash="bh1", pulse_ir_hash="ph1"),
            output_refs={"raw": [dsref]},
        )
        store.finalize_manifest(m)  # write it

        req = ReplayRequest(replay_id="r1", run_id_or_manifest_ref="run1", result_dir=tmp, require_hash_check=False)
        plan = build_replay_plan(req)
        assert "spec" in plan.required_input_refs
        assert plan.required_input_refs["spec"] == "exp1"
        assert "raw" in plan.required_output_refs
        assert any("iq" in uri for uri in plan.required_output_refs.get("raw", []))
        # should not have error diags for core refs (structural)
        assert not any(d.severity == "error" for d in plan.diagnostics)


def test_replay_incomplete_manifest_returns_failed_or_rejected():
    import tempfile
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef
    with tempfile.TemporaryDirectory() as tmp:
        store = FileResultStore(base_dir=tmp)
        m = RunManifest(
            run_id="run2",
            final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="exp2", schema_version="v1"),
            # no compile, no output_refs
        )
        store.finalize_manifest(m)
        req = ReplayRequest(replay_id="r2", run_id_or_manifest_ref="run2", result_dir=tmp)
        res = replay_manifest(req)
        assert res.final_state in ("rejected", "failed")


def test_replay_require_hash_check_missing_dataset_rejected(tmp_path):
    # Use a real L4 run then delete file and check
    from qxtrl.rs import RuntimeService, RunRequest
    from qxtrl.el import create_rabi_experiment_spec
    from qxtrl.cc import minimal_rabi_lab
    lab = minimal_rabi_lab()
    spec = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=lab["chip"],
        l0_wiring_ref=lab["wiring"],
        l0_hw_ref=lab["hardware"],
        l0_safety_ref=lab["safety"],
    )
    rt = RuntimeService(result_base_dir=str(tmp_path))
    l4res = rt.run_once(RunRequest(request_id="hchk", experiment_spec=spec))
    # delete raw
    p = tmp_path / l4res.run_id / "raw" / "iq.json"
    if p.exists():
        p.unlink()
    req = ReplayRequest(replay_id="rh", run_id_or_manifest_ref=l4res.run_id, result_dir=str(tmp_path), require_hash_check=True)
    plan = build_replay_plan(req)
    rres = replay_manifest(req)
    codes = [d.code for d in plan.diagnostics + rres.diagnostics]
    assert "TRH-DATASET-NOT-FOUND" in codes
    assert rres.final_state in ("rejected", "failed")


def test_replay_without_hash_check_can_structurally_inspect_manifest(tmp_path):
    """Even with missing compile hashes or deleted data, require=False allows structural inspect."""
    import tempfile
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef
    with tempfile.TemporaryDirectory() as tmp:
        store = FileResultStore(base_dir=tmp)
        # minimal manifest without compile hashes
        m = RunManifest(
            run_id="run.struct",
            final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="exp.struct", schema_version="v1"),
            compile=CompileManifestRef(bundle_id="b", bundle_hash="", pulse_ir_hash=""),
            # no output_refs to keep simple; structural on spec
        )
        store.finalize_manifest(m)
        req = ReplayRequest(replay_id="rs", run_id_or_manifest_ref="run.struct", result_dir=tmp, require_hash_check=False)
        res = replay_manifest(req)
        # should succeed on structure (core spec present), even if hashes empty
        assert res.final_state == "succeeded"
        assert any(d.code == "TRH-MANIFEST-INCOMPLETE" for d in res.diagnostics)  # warnings still visible
        assert res.output_summary.get("core_refs_present") is False


def test_replay_require_hash_check_hash_mismatch_rejected(tmp_path):
    """Tamper dataset content -> hash computed at write != on disk -> TRH-HASH-MISMATCH + rejected when require=True."""
    import hashlib
    import json
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef, DatasetRef
    from pathlib import Path as _Path
    run_id = "run.mismatch.hash"
    d = _Path(tmp_path) / run_id / "raw"
    d.mkdir(parents=True, exist_ok=True)
    fpath = d / "iq.json"
    payload = {"iq": [{"amp": 0.1, "i": 0.9, "q": 0.1}]}
    good_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
    fpath.write_bytes(good_bytes)
    ch = "sha256:" + hashlib.sha256(good_bytes).hexdigest()[:16]
    dsref = DatasetRef(
        dataset_id="ds1", run_id=run_id,
        logical_uri=f"qxtrl://runs/{run_id}/raw/iq.json",
        content_hash=ch, metadata_hash="sha256:1111111111111111", kind="raw_iq"
    )
    m = RunManifest(
        run_id=run_id,
        final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="exp.m", schema_version="v1"),
        compile=CompileManifestRef(bundle_id="b1", bundle_hash="bh1", pulse_ir_hash="ph1"),
        output_refs={"raw": [dsref]},
    )
    store = FileResultStore(base_dir=str(tmp_path))
    store.finalize_manifest(m)

    # tamper content (different bytes)
    bad_payload = {"iq": [{"amp": 0.1, "i": 0.0, "q": 0.0}]}
    fpath.write_bytes(json.dumps(bad_payload, sort_keys=True).encode("utf-8"))

    req = ReplayRequest(replay_id="rm", run_id_or_manifest_ref=run_id, result_dir=str(tmp_path), require_hash_check=True)
    plan = build_replay_plan(req)
    rres = replay_manifest(req)
    codes = [d.code for d in plan.diagnostics + rres.diagnostics]
    assert "TRH-HASH-MISMATCH" in codes
    assert rres.final_state in ("rejected", "failed")


def test_replay_recorded_and_compare_and_replay_virtual_rejected_until_supported(tmp_path):
    """Non-inspect modes must be rejected with TRH-UNSUPPORTED-MODE (v0.1 scope)."""
    import tempfile
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef
    with tempfile.TemporaryDirectory() as tmp:
        store = FileResultStore(base_dir=tmp)
        m = RunManifest(
            run_id="run.modes",
            final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="exp.modes", schema_version="v1"),
            compile=CompileManifestRef(bundle_id="b", bundle_hash="bh", pulse_ir_hash="ph"),
        )
        store.finalize_manifest(m)
        for mode in ("replay_recorded", "compare", "replay_virtual"):
            req = ReplayRequest(replay_id=f"r{mode}", run_id_or_manifest_ref="run.modes", result_dir=tmp, mode=mode, require_hash_check=False)
            res = replay_manifest(req)
            assert res.final_state == "rejected", f"{mode} should reject"
            assert any(d.code == "TRH-UNSUPPORTED-MODE" for d in res.diagnostics), f"{mode} must carry UNSUPPORTED code"


def test_replay_rejects_cross_run_dataset_ref(tmp_path):
    """Cross-run output_ref (pointing to another run's dataset) must be rejected even if file+hash exist (P1-001)."""
    import hashlib
    import json
    from unittest.mock import patch
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef, DatasetRef
    from pathlib import Path as _Path

    # Create target data file (real bytes + hash)
    target_run = "run.target.data"
    source_run = "run.source.crossref"
    store = FileResultStore(base_dir=str(tmp_path))

    td = _Path(tmp_path) / target_run / "raw"
    td.mkdir(parents=True, exist_ok=True)
    fpath = td / "iq.json"
    payload = {"iq": [1, 2, 3]}
    b = json.dumps(payload, sort_keys=True).encode()
    fpath.write_bytes(b)
    ch = "sha256:" + hashlib.sha256(b).hexdigest()[:16]

    target_ref = DatasetRef(
        dataset_id="t1", run_id=target_run,
        logical_uri=f"qxtrl://runs/{target_run}/raw/iq.json",
        content_hash=ch, metadata_hash="sha256:2222222222222222", kind="raw_iq"
    )
    tm = RunManifest(
        run_id=target_run, final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="exp.t", schema_version="v1"),
        compile=CompileManifestRef(bundle_id="bt", bundle_hash="bht", pulse_ir_hash="pht"),
        output_refs={"raw": [target_ref]},
    )
    store.finalize_manifest(tm)

    # Simulate a source manifest (with cross ref) by patching get_manifest to return a constructed one
    # (L5 validator prevents writing such, but replay must still detect on read/inspect)
    bad_ref = DatasetRef.model_construct(
        dataset_id="badcross", run_id=target_run,
        logical_uri=f"qxtrl://runs/{target_run}/raw/iq.json",
        content_hash=ch, metadata_hash="sha256:2222222222222222", kind="raw_iq"
    )
    fake_source_manifest = RunManifest.model_construct(
        run_id=source_run, final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="exp.s", schema_version="v1"),
        compile=CompileManifestRef(bundle_id="bs", bundle_hash="bhs", pulse_ir_hash="phs"),
        output_refs={"raw": [bad_ref]},
    )

    req = ReplayRequest(replay_id="rc", run_id_or_manifest_ref=source_run, result_dir=str(tmp_path), require_hash_check=True)

    with patch.object(FileResultStore, "get_manifest", return_value=fake_source_manifest):
        plan = build_replay_plan(req)
        rres = replay_manifest(req)

    codes = [d.code for d in plan.diagnostics + rres.diagnostics]
    assert "TRH-DATASET-REF-MISMATCH" in codes
    assert rres.final_state in ("rejected", "failed")


def test_replay_rejects_malformed_dataset_hash(tmp_path):
    """Malformed short/empty hash like 'sha256:' must cause REF-MISMATCH or HASH-MISMATCH under require=True (P1-002)."""
    import json
    from unittest.mock import patch
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef, DatasetRef
    from pathlib import Path as _Path

    run_id = "run.badhash"
    d = _Path(tmp_path) / run_id / "raw"
    d.mkdir(parents=True, exist_ok=True)
    fpath = d / "iq.json"
    fpath.write_bytes(json.dumps({"ok": True}).encode())
    # Use malformed hash in the ref (file exists, but hash in manifest is bad).
    # Use model_construct to simulate a manifest that bypassed normal validation (e.g. hand-edited json).
    badref = DatasetRef.model_construct(
        dataset_id="b1", run_id=run_id,
        logical_uri=f"qxtrl://runs/{run_id}/raw/iq.json",
        content_hash="sha256:", metadata_hash="sha256:3333333333333333"
    )
    store = FileResultStore(base_dir=str(tmp_path))
    # Write the data file (for the check to reach hash stage)
    # Do not rely on finalize/get which will validate and reject bad hash ref.
    # Instead patch get_manifest to return a manifest carrying the bad-ref (model_construct)
    store.create_run(run_id=run_id)  # ensure dir
    # write the iq file
    (_Path(tmp_path) / run_id / "raw" / "iq.json").write_bytes(json.dumps({"ok": True}).encode())

    fake_m = RunManifest.model_construct(
        run_id=run_id, final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="exp.bad", schema_version="v1"),
        compile=CompileManifestRef(bundle_id="bb", bundle_hash="bhb", pulse_ir_hash="phb"),
        output_refs={"raw": [badref]},
    )

    req = ReplayRequest(replay_id="rb", run_id_or_manifest_ref=run_id, result_dir=str(tmp_path), require_hash_check=True)
    with patch.object(FileResultStore, "get_manifest", return_value=fake_m):
        plan = build_replay_plan(req)
        rres = replay_manifest(req)
    codes = [d.code for d in plan.diagnostics + rres.diagnostics]
    assert any(c in ("TRH-DATASET-REF-MISMATCH", "TRH-HASH-MISMATCH") for c in codes)
    assert rres.final_state in ("rejected", "failed")


def test_replay_structural_inspect_reports_core_refs_present_false_when_output_refs_missing(tmp_path):
    """P2-003: !require + missing output_refs must report core_refs_present=False (even if succeeded)."""
    import tempfile
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef
    with tempfile.TemporaryDirectory() as tmp:
        store = FileResultStore(base_dir=tmp)
        m = RunManifest(
            run_id="run.noout",
            final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="exp.noout", schema_version="v1"),
            # deliberately no compile and no output_refs
        )
        store.finalize_manifest(m)
        req = ReplayRequest(replay_id="rno", run_id_or_manifest_ref="run.noout", result_dir=tmp, require_hash_check=False)
        res = replay_manifest(req)
        assert res.final_state == "succeeded"
        assert res.output_summary.get("core_refs_present") is False


def test_replay_rejects_absolute_path_without_echoing_source_manifest_ref(tmp_path):
    """P2-004: absolute/unsafe ref must reject and NOT echo the raw path into source_manifest_ref."""
    req = ReplayRequest(replay_id="ra", run_id_or_manifest_ref="/tmp/run.foo/manifest.json", result_dir=str(tmp_path))
    plan = build_replay_plan(req)
    res = replay_manifest(req)
    assert res.final_state in ("rejected", "failed")
    assert any(d.code == "TRH-INPUT-SCHEMA" for d in res.diagnostics)
    assert plan.source_manifest_ref == "invalid"
    assert res.plan.source_manifest_ref == "invalid"
    # must not contain the bad path
    assert "/tmp" not in str(plan.source_manifest_ref)
    assert "/tmp" not in str(res.plan.source_manifest_ref)


def test_dataset_ref_rejects_short_or_malformed_hash():
    """L5 DatasetRef validator rejects bad hashes (per P1-002)."""
    from pydantic import ValidationError
    from qxtrl.ds.contracts.manifest import DatasetRef
    bad_cases = [
        {"content_hash": "", "metadata_hash": "sha256:0000000000000000"},
        {"content_hash": "sha256:", "metadata_hash": "sha256:0000000000000000"},
        {"content_hash": "sha256:abc", "metadata_hash": "sha256:0000000000000000"},  # too short
        {"content_hash": "sha256:GGGGGGGGGGGGGGGG", "metadata_hash": "sha256:0000000000000000"},  # non-hex
        {"content_hash": "sha256:0123456789abcdef", "metadata_hash": "not-a-hash"},
    ]
    for case in bad_cases:
        try:
            DatasetRef(
                dataset_id="d", run_id="r",
                logical_uri="qxtrl://runs/r/raw/x.json",
                **case
            )
            assert False, f"should have rejected {case}"
        except ValidationError:
            pass


def test_run_manifest_rejects_output_ref_run_id_mismatch():
    """L5 RunManifest validator rejects output_refs whose run_id or uri run segment != own run_id."""
    from pydantic import ValidationError
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, DatasetRef
    good_ref = DatasetRef(
        dataset_id="g", run_id="run.good",
        logical_uri="qxtrl://runs/run.good/raw/iq.json",
        content_hash="sha256:0000000000000000", metadata_hash="sha256:1111111111111111"
    )
    m = RunManifest(
        run_id="run.good", final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="e", schema_version="v1"),
        output_refs={"raw": [good_ref]},
    )
    assert m.run_id == "run.good"

    # bad cross
    bad_ref = DatasetRef.model_construct(
        dataset_id="b", run_id="run.other",
        logical_uri="qxtrl://runs/run.other/raw/iq.json",
        content_hash="sha256:0000000000000000", metadata_hash="sha256:1111111111111111"
    )
    try:
        RunManifest(
            run_id="run.good", final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="e", schema_version="v1"),
            output_refs={"raw": [bad_ref]},
        )
        assert False, "RunManifest should reject cross-run ref"
    except ValidationError:
        pass


def test_replay_accepts_dataset_hash_length_16(tmp_path):
    """L7 replay with require=True accepts 16-char truncated hash (current FileResultStore MVP format)."""
    import hashlib
    import json
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef, DatasetRef
    from pathlib import Path as _Path

    run_id = "run.hash16"
    d = _Path(tmp_path) / run_id / "raw"
    d.mkdir(parents=True, exist_ok=True)
    fpath = d / "iq.json"
    payload = {"i": 1}
    b = json.dumps(payload, sort_keys=True).encode("utf-8")
    fpath.write_bytes(b)

    # 16-char as produced by FileResultStore
    full = hashlib.sha256(b).hexdigest()
    ch16 = "sha256:" + full[:16]
    dsref = DatasetRef(
        dataset_id="d16", run_id=run_id,
        logical_uri=f"qxtrl://runs/{run_id}/raw/iq.json",
        content_hash=ch16, metadata_hash="sha256:" + "a" * 16
    )
    m = RunManifest(
        run_id=run_id, final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="e16", schema_version="v1"),
        compile=CompileManifestRef(bundle_id="b16", bundle_hash="h16", pulse_ir_hash="p16"),
        output_refs={"raw": [dsref]},
    )

    store = FileResultStore(base_dir=str(tmp_path))
    store.finalize_manifest(m)  # writes with its own 16-char, but we use matching ref

    req = ReplayRequest(replay_id="r16", run_id_or_manifest_ref=run_id, result_dir=str(tmp_path), require_hash_check=True)
    _ = build_replay_plan(req)
    res = replay_manifest(req)

    assert res.final_state == "succeeded"
    assert not any(d.code in ("TRH-HASH-MISMATCH", "TRH-DATASET-REF-MISMATCH") for d in res.diagnostics)


def test_replay_accepts_dataset_hash_length_64(tmp_path):
    """L7 replay with require=True accepts full 64-char hash (L5 validator allows it; L7 now supports exact match)."""
    import hashlib
    import json
    from unittest.mock import patch
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef, CompileManifestRef, DatasetRef
    from pathlib import Path as _Path

    run_id = "run.hash64"
    d = _Path(tmp_path) / run_id / "raw"
    d.mkdir(parents=True, exist_ok=True)
    fpath = d / "iq.json"
    payload = {"q": 99}
    b = json.dumps(payload, sort_keys=True).encode("utf-8")
    fpath.write_bytes(b)

    full = hashlib.sha256(b).hexdigest()
    ch64 = "sha256:" + full  # full 64 hex chars
    dsref = DatasetRef(
        dataset_id="d64", run_id=run_id,
        logical_uri=f"qxtrl://runs/{run_id}/raw/iq.json",
        content_hash=ch64, metadata_hash="sha256:" + "b" * 16
    )
    m = RunManifest(
        run_id=run_id, final_state="succeeded",
        experiment=ExperimentManifestRef(spec_id="e64", schema_version="v1"),
        compile=CompileManifestRef(bundle_id="b64", bundle_hash="h64", pulse_ir_hash="p64"),
        output_refs={"raw": [dsref]},
    )

    store = FileResultStore(base_dir=str(tmp_path))
    # Write the dataset dir structure manually since we use 64 (store would write 16)
    # but to have file present, and patch the manifest load
    store.create_run(run_id=run_id)

    req = ReplayRequest(replay_id="r64", run_id_or_manifest_ref=run_id, result_dir=str(tmp_path), require_hash_check=True)

    # Patch get to return our 64-hash manifest (L5 would accept the DatasetRef)
    with patch.object(FileResultStore, "get_manifest", return_value=m):
        _ = build_replay_plan(req)
        res = replay_manifest(req)

    assert res.final_state == "succeeded"
    assert not any(d.code in ("TRH-HASH-MISMATCH", "TRH-DATASET-REF-MISMATCH") for d in res.diagnostics)


def test_replay_no_duplicate_manifest_incomplete_when_require_and_missing_compile(tmp_path):
    """P2-002: When require_hash_check=True and compile hashes missing, only one TRH-MANIFEST-INCOMPLETE error (no dups)."""
    import tempfile
    from qxtrl.ds import FileResultStore
    from qxtrl.ds.contracts.manifest import RunManifest, ExperimentManifestRef
    with tempfile.TemporaryDirectory() as tmp:
        store = FileResultStore(base_dir=tmp)
        m = RunManifest(
            run_id="run.dup",
            final_state="succeeded",
            experiment=ExperimentManifestRef(spec_id="e.dup", schema_version="v1"),
            # no compile => missing bundle/pulse hashes
        )
        store.finalize_manifest(m)
        req = ReplayRequest(replay_id="rd", run_id_or_manifest_ref="run.dup", result_dir=tmp, require_hash_check=True)
        res = replay_manifest(req)
        error_incompletes = [d for d in res.diagnostics if d.code == "TRH-MANIFEST-INCOMPLETE" and d.severity == "error"]
        # At most one (the require check one); previously the re-assert added a duplicate
        assert len(error_incompletes) <= 1
        assert res.final_state in ("rejected", "failed")
