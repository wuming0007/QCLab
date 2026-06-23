"""Example L0 objects for tests, docs and MVP demo.

- public_example_* : from schema example doc, explicitly NOT usable_for_control
- minimal_lab_rabi : smallest valid objects that pass all validators for virtual Rabi demo
"""

from __future__ import annotations

from qxtrl.cc.models import (
    Channel,
    ChannelCapability,
    ChipModel,
    DataQuality,
    Device,
    HardwareInventory,
    Identity,
    QubitElement,
    SafetyPolicy,
    SourceRef,
    WiringEdge,
    WiringGraph,
)
from qxtrl.cc.quantity import Quantity


def public_willow_chip_example() -> ChipModel:
    """Public placeholder only. Matches QXtrl_L0契约层_schema示例_Willow_Heron.md"""
    ident = Identity(
        id="public_google_willow_chipmodel_example",
        display_name="Google Willow public chip model placeholder",
        vendor="Google Quantum AI",
        source_kind="public_example",
        source_refs=[
            SourceRef(label="Google Willow announcement", url="https://blog.google/technology/research/google-willow-quantum-chip/")
        ],
    )
    dq = DataQuality(confidence="public_fact_plus_placeholders", usable_for_control=False, status="draft")
    qubits = [QubitElement(element_id=f"q{i:03d}") for i in range(105)]
    return ChipModel(
        identity=ident,
        data_quality=dq,
        qubits=qubits,
        physical_qubit_count=105,
        modality="superconducting",
    )


def make_rabi_lab(qubit_id: str = "q001", freq_hz: float = 5.123e9) -> dict[str, object]:
    """Rehearsal-friendly L0 lab builder.

    Simulates the "录入" step for a new chip / specific qubit.
    Returns objects that can be passed directly into ExperimentSpec l0_*_ref.
    """
    station = "station.rehearsal01"
    chip_id = f"chip.rehearsal.{qubit_id}"

    qubit = QubitElement(
        element_id=qubit_id,
        display_name=f"Q{qubit_id[1:]}",
        frequency=Quantity(value=freq_hz, unit="Hz", uncertainty=5e6, source="rehearsal_measured"),
    )
    chip = ChipModel(
        identity=Identity(id=chip_id, display_name=f"Rehearsal chip for {qubit_id}", source_kind="simulated"),
        data_quality=DataQuality(confidence="measured", usable_for_control=True, status="approved", approved_by="lab-engineer", approved_at="2026-06-22T00:00:00Z"),
        qubits=[qubit],
    )

    xy_line = f"line.xy.{qubit_id}"
    ro_line = f"line.ro.rr_{qubit_id}"

    edge_xy = WiringEdge(
        line_id=xy_line,
        role="drive_iq",
        endpoints={"chip_element": qubit_id, "hardware_channels": {"i": f"chan.awg.demo.out01", "q": f"chan.awg.demo.out02"}},
        status="approved",
        usable_for_control=True,
    )
    edge_ro = WiringEdge(
        line_id=ro_line,
        role="readout",
        endpoints={"chip_element": f"rr_{qubit_id}", "hardware_channels": {"adc": "chan.adc.demo.in01"}},
        status="approved",
        usable_for_control=True,
    )
    wiring = WiringGraph(
        identity=Identity(id=f"wiring.{chip_id}", display_name=f"Rehearsal wiring for {qubit_id}"),
        data_quality=DataQuality(confidence="measured", usable_for_control=True, status="approved", approved_by="lab-engineer", approved_at="2026-06-22T00:00:00Z"),
        edges=[edge_xy, edge_ro],
    )

    dev_awg = Device(device_id="dev.awg.demo", device_type="awg", status="approved")
    dev_adc = Device(device_id="dev.adc.demo", device_type="adc", status="approved")
    ch_i = Channel(channel_id="chan.awg.demo.out01", capabilities=ChannelCapability(signal_kind="analog_iq"))
    ch_q = Channel(channel_id="chan.awg.demo.out02", capabilities=ChannelCapability(signal_kind="analog_iq"))
    ch_adc = Channel(channel_id="chan.adc.demo.in01", capabilities=ChannelCapability(signal_kind="adc_input"))
    hw = HardwareInventory(
        identity=Identity(id=f"hw.{station}", display_name="Rehearsal instruments"),
        data_quality=DataQuality(confidence="measured", usable_for_control=True, status="approved", approved_by="lab-engineer", approved_at="2026-06-22T00:00:00Z"),
        devices=[dev_awg, dev_adc],
        channels=[ch_i, ch_q, ch_adc],
    )

    policy = SafetyPolicy(
        identity=Identity(id=f"safety.{station}", display_name="Rehearsal safety"),
        data_quality=DataQuality(confidence="measured", usable_for_control=True, status="approved", approved_by="demo-admin", approved_at="2026-06-22T00:00:00Z"),
        applies_to={"station": station, "chip": chip_id},
        operation_classes={
            "simulation": {"allowed": True, "requires_approval": False},
            "replay": {"allowed": True, "requires_approval": False},
        },
    )

    return {
        "chip": chip,
        "wiring": wiring,
        "hardware": hw,
        "safety": policy,
        "target_qubit": qubit_id,
        "drive_line": xy_line,
        "readout_line": ro_line,
    }


# Back-compat for existing demos
def minimal_rabi_lab() -> dict[str, object]:
    return make_rabi_lab("q000")
