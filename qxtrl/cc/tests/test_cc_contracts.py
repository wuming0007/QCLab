"""CC (L0 Core Contracts) tests (MVP scope).

Covers:
- ID validation rules (R-*)
- Quantity
- Schema version
- usable_for_control + missing => deny
- Core models roundtrip + validation
- minimal Rabi lab example
- public example is unusable
"""

import pytest

from qxtrl.cc import (
    ChipModel,
    CouplerElement,
    DataQuality,
    Device,
    HardwareInventory,
    Identity,
    L0SnapshotRef,
    QubitElement,
    QXtrlValidationError,
    Quantity,
    ResonatorElement,
    SafetyPolicy,
    WiringEdge,
    WiringGraph,
    validate_element_id,
    validate_line_id,
    validate_schema_version,
)
from qxtrl.cc.examples import minimal_rabi_lab, public_willow_chip_example
from qxtrl.cc.validators import KNOWN_UNITS, is_usable_for_control
from pydantic import ValidationError as PydanticValidationError


def test_known_units_nonempty():
    assert "Hz" in KNOWN_UNITS
    assert "Sa/s" in KNOWN_UNITS


def test_quantity_basic_and_unknown():
    q1 = Quantity(value=4.2e9, unit="Hz", uncertainty=1e6)
    assert q1.value == 4.2e9
    assert not q1.is_unknown()

    q2 = Quantity(value="unknown", unit="V")
    assert q2.is_unknown()

    with pytest.raises(QXtrlValidationError):
        Quantity(value=1.0, unit="bogus_unit")


def test_id_validators():
    assert validate_element_id("q000") == "q000"
    assert validate_element_id("rr_q007") == "rr_q007"
    assert validate_element_id("tc_q003_q004") == "tc_q003_q004"

    with pytest.raises(QXtrlValidationError):
        validate_element_id("tc_q004_q003")  # unsorted

    with pytest.raises(QXtrlValidationError):
        validate_element_id("Q001")  # upper + wrong format

    assert validate_line_id("line.xy.q000") == "line.xy.q000"
    assert validate_line_id("line.ro.rr_q000") == "line.ro.rr_q000"

    with pytest.raises(QXtrlValidationError):
        validate_line_id("chan.awg.foo.out01")


def test_schema_version():
    assert validate_schema_version("qxtrl.cc.ChipModel/v0.1")
    with pytest.raises(QXtrlValidationError):
        validate_schema_version("wrong.version")


def test_schema_version_must_match_concrete_model_type():
    """Core L0 contract: object type and schema_version name must be bound.

    Previously ChipModel(schema_version="qxtrl.cc.HardwareInventory/v0.1") would pass.
    """
    from qxtrl.cc.models import ChipModel, HardwareInventory, WiringGraph, SafetyPolicy

    good_identity = Identity(id="test.obj01", display_name="Test")
    good_dq = DataQuality(usable_for_control=False)

    # Wrong type name must be rejected (Literal + runtime check)
    with pytest.raises((PydanticValidationError, QXtrlValidationError)):
        ChipModel(schema_version="qxtrl.cc.HardwareInventory/v0.1", identity=good_identity, data_quality=good_dq, qubits=[])

    with pytest.raises((PydanticValidationError, QXtrlValidationError)):
        HardwareInventory(schema_version="qxtrl.cc.ChipModel/v0.1", identity=good_identity, data_quality=good_dq)

    with pytest.raises((PydanticValidationError, QXtrlValidationError)):
        WiringGraph(schema_version="qxtrl.cc.SafetyPolicy/v0.1", identity=good_identity, data_quality=good_dq)

    with pytest.raises((PydanticValidationError, QXtrlValidationError)):
        SafetyPolicy(schema_version="qxtrl.cc.WiringGraph/v0.1", identity=good_identity, data_quality=good_dq)

    # Correct ones still work
    c = ChipModel(schema_version="qxtrl.cc.ChipModel/v0.1", identity=good_identity, data_quality=good_dq, qubits=[])
    assert c.schema_version == "qxtrl.cc.ChipModel/v0.1"

    h = HardwareInventory(schema_version="qxtrl.cc.HardwareInventory/v0.1", identity=good_identity, data_quality=good_dq)
    assert h.schema_version == "qxtrl.cc.HardwareInventory/v0.1"


def test_chip_model_validation_and_require():
    chip = public_willow_chip_example()
    assert chip.physical_qubit_count == 105
    assert not chip.data_quality.usable_for_control

    # usable without approval must fail at DataQuality level (enforced by R-004)
    with pytest.raises(QXtrlValidationError):
        DataQuality(usable_for_control=True, status="draft")

    # also verify require_usable_for_control raises for non-usable objects
    chip = public_willow_chip_example()
    with pytest.raises(QXtrlValidationError):
        chip.require_usable_for_control(context="test")


def test_minimal_rabi_lab_is_valid():
    objs = minimal_rabi_lab()
    chip: ChipModel = objs["chip"]
    wiring: WiringGraph = objs["wiring"]
    hw: HardwareInventory = objs["hardware"]
    safety: SafetyPolicy = objs["safety"]

    # All must validate on construction (already done in factory)
    chip.require_usable_for_control(context="mvp_demo")
    wiring.require_usable_for_control(context="mvp_demo")
    hw.require_usable_for_control(context="mvp_demo")
    safety.require_usable_for_control(context="mvp_demo")

    assert chip.get_qubit("q000").element_id == "q000"
    assert "line.xy.q000" in [e.line_id for e in wiring.edges]
    assert safety.allows_simulation()


def test_snapshot_ref():
    ref = L0SnapshotRef(
        snapshot_id="hw_inv_demo_001",
        schema_version="qxtrl.cc.HardwareInventory/v0.1",
        content_hash="sha256:deadbeef",
        generated_at="2026-06-21T12:00:00Z",
        kind="hardware_inventory",
    )
    assert ref.kind == "hardware_inventory"


def test_safety_deny_by_default_behavior():
    pol = minimal_rabi_lab()["safety"]
    # physical_low_risk should be False in our minimal
    assert not pol.operation_classes["physical_low_risk_calibration"]["allowed"]


def test_quantity_in_model():
    _ = Quantity(value=5.123e9, unit="Hz")
    qb = minimal_rabi_lab()["chip"].qubits[0]
    # already constructed with quantity in factory
    assert qb.frequency is not None
    assert qb.frequency.unit == "Hz"


# ------------------------------------------------------------------
# Contract tests added per L0 implementation review (negative cases)
# ------------------------------------------------------------------

def test_model_rejects_wrong_schema_version_name():
    """P0-001: schema_version name must match the concrete model type."""
    good_id = Identity(id="test.obj01", display_name="Test")
    with pytest.raises((PydanticValidationError, QXtrlValidationError)):
        ChipModel(
            schema_version="qxtrl.cc.HardwareInventory/v0.1",
            identity=good_id,
            data_quality=DataQuality(usable_for_control=False),
            qubits=[],
        )


def test_identity_id_rejects_illegal_chars():
    """P1-001: Identity.id must follow canonical rules (no spaces, must be a-z0-9_.)"""
    with pytest.raises(QXtrlValidationError):
        Identity(id="Bad ID With Spaces", display_name="demo")

    with pytest.raises(QXtrlValidationError):
        Identity(id="UPPERCASE_ID", display_name="demo")

    # valid form
    Identity(id="station.demo01", display_name="demo")


def test_safety_policy_missing_operation_denies():
    """P0-002: missing operation_classes entries must deny (missing => deny)"""
    policy = SafetyPolicy(
        identity=Identity(id="safety.demo01", display_name="demo"),
        data_quality=DataQuality(usable_for_control=False),
        operation_classes={},  # nothing declared
    )
    assert not policy.allows_simulation()
    assert not policy.allows_replay()
    # Explicit True only when declared allowed
    policy2 = SafetyPolicy(
        identity=Identity(id="safety.demo02", display_name="demo"),
        data_quality=DataQuality(usable_for_control=False),
        operation_classes={"simulation": {"allowed": True}},
    )
    assert policy2.allows_simulation()


def test_wiring_edge_rejects_invalid_channel_id():
    """P0-003: WiringEdge endpoint hardware channels must have valid channel IDs."""
    with pytest.raises(QXtrlValidationError):
        WiringEdge(
            line_id="line.xy.q000",
            endpoints={
                "chip_element": "q000",
                "hardware_channels": {"i": "not_a_channel"},  # invalid format
            },
        )


def test_wiring_graph_requires_approved_edges_for_control():
    """Edges marked usable_for_control must be approved."""
    # must provide full channels for the role now
    edge = WiringEdge(
        line_id="line.xy.q000",
        endpoints={
            "chip_element": "q000",
            "hardware_channels": {"i": "chan.awg.demo.out01", "q": "chan.awg.demo.out02"},
        },
        status="draft",
        usable_for_control=True,
    )
    with pytest.raises(QXtrlValidationError):
        WiringGraph(
            identity=Identity(id="wiring.test01", display_name="test"),
            data_quality=DataQuality(usable_for_control=False),
            edges=[edge],
        )


def test_hardware_inventory_control_requires_channels_or_virtual_flag():
    """P1-002: usable_for_control=True should require channels (virtual demos must still declare representative ones)."""
    dev = Device(device_id="dev.awg.demo", device_type="awg")
    with pytest.raises(QXtrlValidationError):
        HardwareInventory(
            identity=Identity(id="hw.demo01", display_name="demo"),
            data_quality=DataQuality(
                confidence="measured",
                usable_for_control=True,
                status="approved",
                approved_by="tester",
                approved_at="2026-06-21T00:00:00Z",
            ),
            devices=[dev],
            channels=[],  # should be rejected
        )


# ------------------------------------------------------------------
# Tests for remaining core issues from re-review
# ------------------------------------------------------------------

def test_data_quality_mutation_and_gate_bypass():
    """DataQuality assignment mutation and L0Base.require_usable_for_control gate must not be bypassable."""
    # Direct mutation on DataQuality must be rejected by its validator
    dq = DataQuality(usable_for_control=False, status="draft")
    with pytest.raises(QXtrlValidationError):
        dq.usable_for_control = True

    # Cannot even construct an invalid DataQuality (stronger gate)
    with pytest.raises(QXtrlValidationError):
        DataQuality(usable_for_control=True, status="draft")

    # require_usable_for_control on a non-usable object raises
    obj = ChipModel(
        identity=Identity(id="chip.mut02", display_name="m"),
        data_quality=DataQuality(usable_for_control=False),
        qubits=[],
    )
    with pytest.raises(QXtrlValidationError):
        obj.require_usable_for_control()

    # Bypassing via raw data on L0 model_validate is rejected by the field validator
    with pytest.raises(QXtrlValidationError):
        ChipModel.model_validate({
            "identity": {"id": "chip.mut01", "display_name": "m"},
            "data_quality": {"usable_for_control": True, "status": "draft"},
            "qubits": [],
        })


def test_data_quality_assignment_cannot_break_control_approval():
    """From re-review: mutating an approved DataQuality must not be allowed to break the gate."""
    dq = DataQuality(
        usable_for_control=True,
        status="approved",
        approved_by="tester",
        approved_at="2026-06-21T00:00:00Z",
    )
    with pytest.raises((QXtrlValidationError, Exception)):  # pydantic ValidationError or our error
        dq.status = "disabled"


def test_require_usable_for_control_checks_status_and_approval():
    """require_usable_for_control must delegate to full governance check, not just the bool."""
    chip = ChipModel(
        identity=Identity(id="chip.demo_mutation", display_name="demo"),
        data_quality=DataQuality(
            usable_for_control=True,
            status="approved",
            approved_by="tester",
            approved_at="2026-06-21T00:00:00Z",
        ),
        qubits=[],
    )
    # Replacing with a non-approved one should make the gate fail
    chip.data_quality = DataQuality(usable_for_control=False)
    with pytest.raises(QXtrlValidationError):
        chip.require_usable_for_control(context="physical")


def test_is_usable_for_control_dict_requires_approved_status_and_approver():
    """is_usable_for_control on dict must be strict."""
    assert not is_usable_for_control({"usable_for_control": True})
    assert not is_usable_for_control({"usable_for_control": True, "status": "draft"})
    assert is_usable_for_control(
        {
            "usable_for_control": True,
            "status": "approved",
            "approved_by": "tester",
            "approved_at": "2026-06-21T00:00:00Z",
        }
    )


def test_dataquality_revocation_mechanism():
    """Revocation fields + logic: once revoked, cannot be approved for control."""
    # Normal approved
    dq = DataQuality(
        usable_for_control=True,
        status="approved",
        approved_by="eng",
        approved_at="2026-06-21T00:00:00Z",
    )
    assert dq.is_approved_for_control()
    assert not dq.is_revoked()

    # Revoke properly
    dq.usable_for_control = False
    dq.status = "disabled"
    dq.revoked_by = "admin"
    dq.revoked_at = "2026-06-22T00:00:00Z"
    dq.revocation_reason = "drift"
    assert not dq.is_approved_for_control()
    assert dq.is_revoked()

    # Cannot set usable=True when revoked
    dq2 = DataQuality(revoked_by="a", revoked_at="t", status="disabled")
    with pytest.raises(QXtrlValidationError):
        dq2.usable_for_control = True

    # Construct revoked+usable invalid
    with pytest.raises(QXtrlValidationError):
        DataQuality(
            usable_for_control=True,
            status="approved",
            approved_by="e",
            approved_at="t",
            revoked_by="a",
        )

    # is_usable_for_control dict with revoke
    assert not is_usable_for_control(
        {"usable_for_control": False, "status": "disabled", "revoked_by": "a"}
    )

    # Inconsistent approved + revoked
    with pytest.raises(QXtrlValidationError):
        DataQuality(status="approved", approved_by="e", approved_at="t", revoked_by="a")

    # revoke() helper
    approved = DataQuality(usable_for_control=True, status="approved", approved_by="eng", approved_at="t")
    revoked_copy = approved.revoke(by="admin", at="t2", reason="issue")
    assert not revoked_copy.is_approved_for_control()
    assert revoked_copy.is_revoked()
    assert revoked_copy.status == "disabled"
    assert approved.is_approved_for_control()  # original unchanged


def test_chipmodel_resonator_coupler_topology_consistency():
    """ChipModel must validate resonator attached_to and coupler endpoints against known qubits."""
    base = dict(
        identity=Identity(id="chip.topo01", display_name="t"),
        data_quality=DataQuality(usable_for_control=False),
    )
    # bad resonator
    with pytest.raises(QXtrlValidationError):
        ChipModel(**base, resonators=[ResonatorElement(element_id="rr_q000", attached_to="q999")])

    # bad coupler endpoint
    with pytest.raises(QXtrlValidationError):
        ChipModel(
            **base,
            couplers=[CouplerElement(element_id="tc_q000_q001", endpoints=["q000", "q999"])],
        )

    # good one
    ChipModel(
        **base,
        qubits=[QubitElement(element_id="q000"), QubitElement(element_id="q001")],
        resonators=[ResonatorElement(element_id="rr_q000", attached_to="q000")],
        couplers=[CouplerElement(element_id="tc_q000_q001", endpoints=["q000", "q001"])],
    )


def test_wiringedge_role_channel_minimal_semantics():
    """WiringEdge must enforce minimal channel requirements based on role."""
    # drive_iq requires i+q
    with pytest.raises(QXtrlValidationError):
        WiringEdge(
            line_id="line.xy.q000",
            role="drive_iq",
            endpoints={"chip_element": "q000", "hardware_channels": {"i": "c1"}},
        )

    # readout requires adc
    with pytest.raises(QXtrlValidationError):
        WiringEdge(
            line_id="line.ro.rr_q000",
            role="readout",
            endpoints={"chip_element": "rr_q000", "hardware_channels": {}},
        )

    # good drive_iq
    WiringEdge(
        line_id="line.xy.q000",
        role="drive_iq",
        endpoints={"chip_element": "q000", "hardware_channels": {"i": "chan.awg.demo.out01", "q": "chan.awg.demo.out02"}},
    )


def test_quantity_rejects_bool_nan_inf():
    """Quantity must reject bool, NaN and Inf (and Any must be importable/used)."""
    with pytest.raises(QXtrlValidationError):
        Quantity(value=True, unit="Hz")
    with pytest.raises(QXtrlValidationError):
        Quantity(value=float("nan"), unit="Hz")
    with pytest.raises(QXtrlValidationError):
        Quantity(value=float("inf"), unit="s")
    # good cases
    Quantity(value=1.2, unit="GHz")
    Quantity(value="unknown", unit="V")
