# qxtrl.cc — Core Contracts (L0 / CC)

This package is the foundation for QXtrl.

**Do not implement business logic here.** L0 only defines:
- Stable IDs and naming rules
- Quantity with units
- Core domain models (ChipModel, WiringGraph, HardwareInventory, SafetyPolicy, ...)
- Schema versioning + governance (usable_for_control, source, confidence)
- Typed errors and validators

All L1+ layers import from here.

## Quick start (dev)

```bash
# from repo root
PYTHONPATH=. python3 -c 'from qxtrl.cc import minimal_rabi_lab; print(minimal_rabi_lab()["chip"].identity.id)'
PYTHONPATH=. python3 -m pytest qxtrl/cc/tests/ -q
```

See:
- `docs/planning/QXtrl_L0_Core_Contracts_设计.md`
- `docs/L0_API.md`
- `docs/planning/QXtrl_L0契约层命名与编码规则.md`
- `docs/planning/QXtrl_MVP最薄垂直切片定义.md`

Current version aligns with MVP Rabi on Virtual (no waveforms in these contracts).
