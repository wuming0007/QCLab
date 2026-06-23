"""Rehearsal script for the user's exact vision.

Story:
1. New chip arrives + system is connected.
2. "录入" (pre-settings): record topology, wiring for q001 control/readout lines,
   hardware channels, basic qubit params.
3. Define time-Rabi experiment on q001:
   - Fixed amplitude 0.1 on its drive (control) line
   - Scan pulse width (duration)
   - Readout after pulse
4. Submit the task (virtual execution for rehearsal).
5. Get result.
6. Review / look back: manifest, data, replay inspect.

This demonstrates L0 "录入", L1 spec with explicit lines, full execution + L5/L7 review.
"""

import tempfile
from pathlib import Path

from qxtrl.cc.examples import make_rabi_lab
from qxtrl.el import create_time_rabi_experiment_spec
from qxtrl.rs import RuntimeService, RunRequest
from qxtrl.ds import FileResultStore
from qxtrl.trh import replay_manifest, ReplayRequest


def main():
    print("=" * 70)
    print("QXtrl Rehearsal: New chip → 录入 L0 → Time Rabi on q001 → Review")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        # ============================================
        # Step 1 & 2: "录入" — record the new chip setup
        # ============================================
        print("\n[1] Pre-settings / 录入 (simulated by constructing L0 objects)")
        lab = make_rabi_lab(qubit_id="q001", freq_hz=5.234e9)
        print("  Recorded:")
        print(f"    Chip     : {lab['chip'].identity.id}")
        print(f"    Qubit    : {lab['target_qubit']} @ {lab['chip'].qubits[0].frequency}")
        print(f"    Drive    : {lab['drive_line']}")
        print(f"    Readout  : {lab['readout_line']}")
        print(f"    Wiring   : {lab['wiring'].identity.id} ({len(lab['wiring'].edges)} edges)")
        print(f"    Hardware : {lab['hardware'].identity.id}")
        print(f"    Safety   : simulation allowed")

        # ============================================
        # Step 3: Define the experiment (time Rabi)
        # ============================================
        print("\n[2] Define experiment: Time Rabi on q001 (fixed amp=0.1, scan duration)")
        spec = create_time_rabi_experiment_spec(
            qubit_id="q001",
            drive_line_id=lab["drive_line"],
            readout_line_id=lab["readout_line"],
            durations=[10.0, 20.0, 30.0, 40.0, 50.0, 80.0, 120.0],
            fixed_amplitude=0.1,
            shots=1024,
            l0_chip_model_ref=lab["chip"],
            l0_wiring_ref=lab["wiring"],
            l0_hw_ref=lab["hardware"],
            l0_safety_ref=lab["safety"],
        )
        print(f"    spec_id: {spec.spec_id}")
        print(f"    scan parameter: {spec.plan.scan.axes[0].parameter_ref}")
        print(f"    fixed amp in Do: {spec.do.parameters.get('pulse_amplitude')}")

        # ============================================
        # Step 4: Submit
        # ============================================
        print("\n[3] Submit task (virtual execution)")
        runtime = RuntimeService(result_base_dir=tmpdir)
        req = RunRequest(
            request_id=f"req_{spec.spec_id}",
            experiment_spec=spec,
            backend_id="backend.virtual.rabi_mvp",
            mode="virtual",
        )
        result = runtime.run_once(req)
        print(f"    final_state: {result.final_state}")
        print(f"    manifest_ref: {result.manifest_ref}")

        # ============================================
        # Step 5 + 6: Get result + Review / look back
        # ============================================
        print("\n[4] Review results (L5 manifest + L7 replay inspect)")

        store = FileResultStore(base_dir=tmpdir)
        m = store.get_manifest(result.run_id)
        print(f"    Manifest has output groups: {list(m.output_refs.keys())}")
        print(f"    Compile: bundle={m.compile.bundle_id}, pulse_ir_hash={m.compile.pulse_ir_hash}")

        # Replay inspect
        for req_hash in (True, False):
            rres = replay_manifest(ReplayRequest(
                replay_id=f"review-{req_hash}",
                run_id_or_manifest_ref=result.manifest_ref,
                result_dir=tmpdir,
                mode="inspect",
                require_hash_check=req_hash,
            ))
            print(f"    Replay (require_hash_check={req_hash}): {rres.final_state}  "
                  f"core_refs={rres.output_summary.get('core_refs_present')}")

        print("\n" + "=" * 70)
        print("Rehearsal complete. The full operator story ran:")
        print("  录入 L0 objects for q001 → define time-Rabi spec → submit → review results")
        print("=" * 70)


if __name__ == "__main__":
    main()
