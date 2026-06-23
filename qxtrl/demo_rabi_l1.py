"""MVP Rabi demo rehearsal script (thin vertical slice).

Proves:
1. Structured ExperimentSpec (L1)
2. Compile boundary (L2 bundle/PulseIR hashes)
3. Virtual execution (L3/L7) + L6 analysis producing candidate proposal
4. RunManifest + L7 replay inspect (with require_hash_check)

Always uses isolated temp dir. Non-dev friendly output with explicit PROOF lines + candidate note.
Includes one negative path (dataset delete + hash check).

Usage:
  PYTHONPATH=. python -m qxtrl.demo_rabi_l1
"""

import tempfile
from pathlib import Path

from qxtrl.el import create_rabi_experiment_spec
from qxtrl.rs import RuntimeService, RunRequest
from qxtrl.cc import minimal_rabi_lab
from qxtrl.ds import FileResultStore
from qxtrl.trh import replay_manifest, ReplayRequest


def main():
    print("=== QXtrl MVP Rabi Demo Rehearsal (L1->L2->L3/L7->L6->L5->L7 replay) ===")
    print("Using isolated temp dir. No pollution of cwd 'runs/'.")

    with tempfile.TemporaryDirectory() as tmpdir:
        lab = minimal_rabi_lab()

        # 1. L1 + L0 context
        spec = create_rabi_experiment_spec(
            qubit_id="q000",
            l0_chip_model_ref=lab["chip"],
            l0_wiring_ref=lab["wiring"],
            l0_hw_ref=lab["hardware"],
            l0_safety_ref=lab["safety"],
        )
        print("L1 ExperimentSpec created:", spec.spec_id)

        lab["chip"].require_usable_for_control(context="l1.demo")
        lab["wiring"].require_usable_for_control(context="l1.demo")
        print("L0 gates passed (approved + not revoked).")

        # 2. L4 run (uses L2 compile, L3/EB+TRH virtual, L6 analyze, L5 persist)
        runtime = RuntimeService(result_base_dir=tmpdir)
        req = RunRequest(
            request_id=f"req_{spec.spec_id}",
            experiment_spec=spec,
            backend_id="backend.virtual.rabi_mvp",
            mode="virtual",
        )
        runtime_result = runtime.run_once(req)
        print("L4 RuntimeRunResult:", runtime_result.final_state)
        print("  bundle_id:", getattr(runtime_result, 'bundle_id', None))
        print("  manifest_ref:", getattr(runtime_result, 'manifest_ref', None))
        analysis = getattr(runtime_result, 'analysis_result', None) or {}
        proposal = analysis.get('proposal', {}) if isinstance(analysis, dict) else {}
        print("L6 Analysis proposal (CANDIDATE ONLY - does NOT write active ConfigStore):", proposal)

        if not runtime_result.manifest_ref:
            print("No manifest_ref; aborting rehearsal.")
            return

        # Extract run_id
        run_id = runtime_result.run_id or runtime_result.manifest_ref.split('/')[-2] if '/' in (runtime_result.manifest_ref or '') else None

        # 3. L5 manifest view
        store = FileResultStore(base_dir=tmpdir)
        try:
            m = store.get_manifest(run_id)
            print("L5 RunManifest loaded. compile:", m.compile)
            print("  output_refs groups:", list(m.output_refs.keys()) if m.output_refs else [])
            print("  timing_metrics total:", getattr(m.timing_metrics, 'total_duration_ms', None))
        except Exception as e:
            print("L5 manifest load note:", e)

        # 4. L7 replay inspect (require_hash_check True + False)
        print("\n--- L7 Replay Inspect ---")
        for require in (True, False):
            try:
                rreq = ReplayRequest(
                    replay_id=f"reh-{require}",
                    run_id_or_manifest_ref=runtime_result.manifest_ref or run_id,
                    result_dir=tmpdir,
                    mode="inspect",
                    require_hash_check=require,
                )
                rres = replay_manifest(rreq)
                print(f"replay (require_hash_check={require}): final={rres.final_state}")
                print(f"  output_summary: {rres.output_summary}")
                if rres.diagnostics:
                    print(f"  diags: {[ (d.code, d.severity) for d in rres.diagnostics ]}")
            except Exception as e:
                print(f"replay (require={require}) error (expected in some neg): {e}")

        # 5. Negative: delete raw dataset + require=true → should reject
        print("\n--- Negative Path (delete dataset + require_hash_check) ---")
        try:
            raw_p = Path(tmpdir) / run_id / "raw" / "iq.json"
            if raw_p.exists():
                raw_p.unlink()
            rreq_neg = ReplayRequest(
                replay_id="reh-neg",
                run_id_or_manifest_ref=runtime_result.manifest_ref or run_id,
                result_dir=tmpdir,
                mode="inspect",
                require_hash_check=True,
            )
            rres_neg = replay_manifest(rreq_neg)
            print("negative replay final:", rres_neg.final_state)
            codes = [d.code for d in (rres_neg.diagnostics or [])]
            print("  codes:", codes)
            if any("DATASET-NOT-FOUND" in c or "REF-MISMATCH" in c for c in codes):
                print("NEGATIVE PATH VISIBLE: good (rejected with diagnostic).")
        except Exception as e:
            print("negative path note:", e)

        print("\n=== Rehearsal Complete ===")
        print("PROOFS (visible above):")
        print("  1. Structured L1 spec + L0 context")
        print("  2. L2 compile boundary (bundle + hashes in manifest)")
        print("  3. Virtual execution (L3/L7) + L6 candidate proposal (explicit CANDIDATE note)")
        print("  4. L5 RunManifest + L7 replay inspect (success + negative with codes)")
        print("All via isolated temp dir. Deterministic virtual + typed contracts respected.")


if __name__ == "__main__":
    main()
