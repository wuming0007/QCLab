# qxtrl.el — Experiment Language (L1 / EL)

L1 Experiment Language defines structured, versioned, recursive PDCA-based specifications
(`ExperimentSpec`, `AtomSpec` for MVP) for experiment intent.

**Depends on L0/CC (`qxtrl.cc`)** for IDs, units, Quantity, snapshots, approval gates, and errors.

Does **not**:
- Generate final waveforms (that's L2)
- Perform device I/O or scheduling (L3/L4)
- Persist data or write active config (L5/L6/L9)
- Implement full Task/Session orchestration (P1+)

See the authoritative design document:
`docs/planning/QXtrl_L1_Experiment_Language_设计.md`

## Quick start (MVP Rabi)

```python
from qxtrl.el import ExperimentSpec, AtomSpec  # etc.
from qxtrl.cc import minimal_rabi_lab  # for L0 examples

# Build a minimal Rabi Atom spec (see design doc for full example)
spec = ExperimentSpec(...)  # populated as per schema

# Later: validate against L0 gates + Registry, emit to L2, etc.
print(spec.schema_version)  # qxtrl.el.ExperimentSpec/v0.1
```

Current focus: MVP Rabi Atom + ExperimentSpec, L0 integration, basic Registry.

## Usage example

```python
from qxtrl.el import create_rabi_experiment_spec, ExperimentSpec
from qxtrl.cc import minimal_rabi_lab

lab = minimal_rabi_lab()
spec: ExperimentSpec = create_rabi_experiment_spec(
    qubit_id="q000",
    l0_chip_model_ref=lab["chip"],
    l0_wiring_ref=lab["wiring"],
    l0_hw_ref=lab["hardware"],
    l0_safety_ref=lab["safety"],
)
print(spec.schema_version)  # qxtrl.el.ExperimentSpec/v0.1
print("plan objective:", spec.plan.objective)
# spec is frozen: use spec.model_copy(...) for derived versions
```