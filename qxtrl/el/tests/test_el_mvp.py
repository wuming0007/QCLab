"""MVP tests for L1/EL Experiment Language, per design doc."""

import pytest

from qxtrl.el import (
    create_rabi_experiment_spec,
    ExperimentSpec,
    ActSpec,
    DoSpec,
    CheckSpec,
    L0ContextRef,
    PlanSpec,
    TargetSpec,
    ScanSpec,
    ScanAxisSpec,
    AcquisitionSpec,
    NodeIOContract,
    TypedRef,
    ParameterProposalTarget,
    PDCAPathItem,
    registry,
)
from qxtrl.cc.errors import QXtrlValidationError
from qxtrl.cc import minimal_rabi_lab, public_willow_chip_example


def test_rabi_atom_spec_validates():
    spec = create_rabi_experiment_spec()
    assert spec.schema_version == "qxtrl.el.ExperimentSpec/v0.1"
    assert spec.node_kind == "atom"
    assert spec.atom is not None
    assert len(spec.children) == 0


def test_experiment_spec_rejects_waveform_array():
    spec = create_rabi_experiment_spec()
    with pytest.raises(QXtrlValidationError):
        bad_do = DoSpec(
            atom_ref=spec.do.atom_ref,
            parameters={"waveform": [0.1, 0.2]},
        )
        # Would be caught in full validation too
        ExperimentSpec(
            **spec.model_dump(exclude={"do"}),
            do=bad_do,
        )


def test_atom_must_not_have_children():
    spec = create_rabi_experiment_spec()
    with pytest.raises((QXtrlValidationError, TypeError, ValueError)):
        bad_data = spec.model_dump()
        bad_data["children"] = [spec.model_dump()]
        ExperimentSpec(**bad_data)


def test_task_session_rejected_in_mvp():
    # Use valid inner specs (so that node_kind is the only MVP violation)
    good_check = CheckSpec(analyzer_ref="a", expected_observation="o", metrics=["pi_amp"], acceptance={"min": 0.1})
    good_act = ActSpec(mode="none")
    good_io = NodeIOContract(consumes=(TypedRef(kind="q", ref="x"),), produces=(TypedRef(kind="obs", ref="y"),))
    with pytest.raises(QXtrlValidationError):
        ExperimentSpec(
            spec_id="bad",
            node_kind="task",
            pdca_path=[],
            l0_context=L0ContextRef(  # minimal valid
                chip_model_ref="c",
                wiring_graph_ref="w",
                hardware_inventory_ref="h",
                safety_policy_ref="s",
            ),
            plan=PlanSpec(objective="x", target=TargetSpec(element_id="q000"), scan=ScanSpec(axes=()), acquisition=AcquisitionSpec(shots=1)),
            do=DoSpec(atom_ref="a"),
            check=good_check,
            act=good_act,
            io=good_io,
        )


def test_registry_resolves_rabi_atom_and_analyzer():
    entry = registry.resolve("qxtrl.atom.rabi_amplitude/v0.1", "qxtrl.el.ExperimentSpec/v0.1")
    assert entry.entry_kind == "atom"

    entry2 = registry.resolve("qxtrl.check.rabi_fit/v0.1", "qxtrl.el.ExperimentSpec/v0.1")
    assert entry2.entry_kind == "analyzer"


def test_scan_axis_rejects_bad_unit_nan_inf_bool():
    # Use a valid parameter_ref so failures come from unit/values (not param ref validator)
    valid_ref = "pulse.drive.amplitude"
    # bad unit
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref=valid_ref, unit="badunit", values=[0.1])

    # empty
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref=valid_ref, unit="a.u.", values=[])

    # NaN/Inf/bool
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref=valid_ref, unit="a.u.", values=[float("nan")])
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref=valid_ref, unit="a.u.", values=[float("inf")])
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref=valid_ref, unit="a.u.", values=[True])


def test_experiment_spec_rejects_bad_target_id():
    with pytest.raises(QXtrlValidationError):
        TargetSpec(element_id="Q000")  # uppercase invalid per L0
    with pytest.raises(QXtrlValidationError):
        TargetSpec(element_id="foo")


def test_node_io_contract_requires_consumes_produces():
    # io without consumes/produces must be rejected at ExperimentSpec level
    spec = create_rabi_experiment_spec()
    with pytest.raises(QXtrlValidationError):
        bad_io = NodeIOContract(consumes=(), produces=())
        ExperimentSpec(
            **spec.model_dump(exclude={"io"}),
            io=bad_io,
        )


def test_physical_context_requires_approved_l0():
    """L0 objects that fail is_approved_for_control / require must cause L1 validation error."""
    good = minimal_rabi_lab()
    # Good objects succeed
    spec_ok = create_rabi_experiment_spec(
        qubit_id="q000",
        l0_chip_model_ref=good["chip"],
        l0_wiring_ref=good["wiring"],
        l0_hw_ref=good["hardware"],
        l0_safety_ref=good["safety"],
    )
    assert spec_ok.spec_id

    # Bad chip (public example not approved for control)
    bad_chip = public_willow_chip_example()
    with pytest.raises(QXtrlValidationError) as exc:
        create_rabi_experiment_spec(
            qubit_id="q000",
            l0_chip_model_ref=bad_chip,
            l0_wiring_ref=good["wiring"],
            l0_hw_ref=good["hardware"],
            l0_safety_ref=good["safety"],
        )
    assert "L0" in str(exc.value) or "L1-L0-GATE" in str(exc.value) or "not approved" in str(exc.value).lower()


def test_io_and_pdca_are_recorded_in_spec():
    spec = create_rabi_experiment_spec()
    assert len(spec.io.consumes) >= 1
    assert len(spec.io.produces) >= 1
    assert len(spec.pdca_path) >= 1
    assert spec.pdca_path[0].node_kind == "atom"


# ------------------------------------------------------------------
# New contract tests per L1 review (P1/P2 findings)
# ------------------------------------------------------------------

def test_schema_version_must_be_exact_v01():
    spec = create_rabi_experiment_spec()
    with pytest.raises(QXtrlValidationError):
        ExperimentSpec(
            **spec.model_dump(exclude={"schema_version"}),
            schema_version="qxtrl.el.ExperimentSpec/v9.9",
        )
    with pytest.raises(QXtrlValidationError):
        ExperimentSpec(
            **spec.model_dump(exclude={"schema_version"}),
            schema_version="qxtrl.el.ExperimentSpec/v0.1.extra",
        )


def test_failed_assignment_does_not_mutate_spec():
    """With frozen=True, assignment after validation must be rejected and leave original intact."""
    spec = create_rabi_experiment_spec()
    original_io = spec.io
    with pytest.raises(Exception):  # pydantic FrozenInstanceError (or subclass)
        spec.io = NodeIOContract(consumes=(), produces=())
    # original must be unchanged
    assert spec.io is original_io
    assert len(spec.io.consumes) > 0


def test_nested_mutation_cannot_break_validated_spec():
    """Nested collections are tuples (immutable); direct mutation must fail."""
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.io.consumes.clear()  # tuple has no clear
    with pytest.raises(Exception):
        spec.io.consumes.append(TypedRef(kind="x", ref="y"))  # tuple immutable
    # state remains valid
    assert len(spec.io.consumes) >= 1


def test_parameter_ref_mvp_path_rules():
    # good pulse
    ax = ScanAxisSpec(axis_id="a", parameter_ref="pulse.drive.amplitude", unit="a.u.", values=(0.1,))
    assert ax.parameter_ref.startswith("pulse.")

    # good calibration
    ax2 = ScanAxisSpec(axis_id="c", parameter_ref="calibration.q000.xy.pi_amp", unit="a.u.", values=(0.1,))
    assert ax2.parameter_ref.startswith("calibration.")

    # bads
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="b", parameter_ref="bad.path.syntax", unit="a.u.", values=(0.1,))
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="b", parameter_ref="bad.path", unit="a.u.", values=(0.1,))
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="b", parameter_ref="foo.bar", unit="a.u.", values=(0.1,))


def test_parameter_ref_element_must_match_target():
    good = create_rabi_experiment_spec(qubit_id="q000")
    assert any(p.parameter_ref.startswith("calibration.q000") for p in good.act.proposal_targets)

    # Bad proposal element
    with pytest.raises(QXtrlValidationError):
        bad_act = ActSpec(
            mode="propose_patch",
            proposal_targets=(ParameterProposalTarget(parameter_ref="calibration.q123.xy.pi_amp", source_metric="pi_amp"),),
        )
        # build minimal valid other pieces
        t = TargetSpec(element_id="q000")
        s = ScanSpec(axes=(ScanAxisSpec(axis_id="x", parameter_ref="pulse.drive.amplitude", unit="a.u.", values=(0.1,)),))
        ExperimentSpec(
            spec_id="badref",
            pdca_path=(PDCAPathItem(node_id="n", node_kind="atom", pdca_phase="do"),),
            l0_context=L0ContextRef(chip_model_ref="c", wiring_graph_ref="w", hardware_inventory_ref="h", safety_policy_ref="s"),
            plan=PlanSpec(objective="o", target=t, scan=s, acquisition=AcquisitionSpec(shots=1)),
            do=DoSpec(atom_ref="a"),
            check=CheckSpec(analyzer_ref="a", expected_observation="o", metrics=("m",), acceptance={"a": 1}),
            act=bad_act,
            io=NodeIOContract(consumes=(TypedRef(kind="q", ref="q000"),), produces=(TypedRef(kind="o", ref="r"),)),
        )


def test_proposal_target_ref_must_be_valid():
    with pytest.raises(QXtrlValidationError):
        ParameterProposalTarget(parameter_ref="invalid", source_metric="x")


def test_coupler_id_uses_element_validator():
    # valid coupler
    ts = TargetSpec(element_id="q000", coupler_id="tc_q000_q001")
    assert ts.coupler_id == "tc_q000_q001"

    # coupler that looks like line must be rejected by element rule
    with pytest.raises(QXtrlValidationError):
        TargetSpec(element_id="q000", coupler_id="line.xy.q000")

    # drive must still be line
    with pytest.raises(QXtrlValidationError):
        TargetSpec(element_id="q000", drive_line_id="q000")  # not a line id


def test_do_spec_rejects_nested_waveform_keys():
    spec = create_rabi_experiment_spec()
    with pytest.raises(QXtrlValidationError):
        bad_do = DoSpec(
            atom_ref=spec.do.atom_ref,
            parameters={"pulse": {"waveform": [0.1, 0.2, 0.3]}},
        )
        ExperimentSpec(**spec.model_dump(exclude={"do"}), do=bad_do)

    with pytest.raises(QXtrlValidationError):
        bad_do2 = DoSpec(
            atom_ref=spec.do.atom_ref,
            compile_hints={"render": {"samples": [1, 2]}},
        )
        ExperimentSpec(**spec.model_dump(exclude={"do"}), do=bad_do2)


def test_registry_schema_prefixes_use_short_codes():
    entry = registry.resolve("qxtrl.check.rabi_fit/v0.1", "qxtrl.el.ExperimentSpec/v0.1")
    assert "qxtrl.l1" not in entry.input_schema
    assert "qxtrl.l6" not in entry.output_schema
    assert entry.input_schema.startswith("qxtrl.el.")
    assert "qxtrl.co" in entry.output_schema or entry.output_schema.startswith("qxtrl.")


def test_check_spec_requires_metrics():
    with pytest.raises(QXtrlValidationError):
        CheckSpec(analyzer_ref="a", expected_observation="o", metrics=(), acceptance={"min": 0.1})


def test_spec_is_frozen_after_creation():
    """Top level ExperimentSpec is frozen."""
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.spec_id = "mutated"


# ------------------------------------------------------------------
# Re-review required tests (P1-010 mutation resistance, P1-011 validated copy, P2-012 param_ref tightening)
# ------------------------------------------------------------------

def test_pdca_path_cannot_be_mutated_after_validation():
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.pdca_path.clear()


def test_scan_axes_cannot_be_cleared_after_validation():
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.plan.scan.axes.clear()


def test_scan_values_cannot_be_mutated_after_validation():
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        # values is now tuple
        spec.plan.scan.axes[0].values.append(999.0)  # tuple has no append
    # also values must not accept bad content via reconstruction
    with pytest.raises(QXtrlValidationError):
        # direct construction with bad value should fail validator
        ScanAxisSpec(axis_id="x", parameter_ref="pulse.drive.amplitude", unit="a.u.", values=(0.1, True))


def test_acquisition_cannot_be_mutated_after_validation():
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.plan.acquisition.shots = -1


def test_check_metrics_cannot_be_mutated_after_validation():
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.check.metrics.clear()


def test_typed_ref_cannot_be_mutated_after_validation():
    spec = create_rabi_experiment_spec()
    with pytest.raises(Exception):
        spec.io.consumes[0].ref = "mutated"


def test_validated_copy_revalidates():
    spec = create_rabi_experiment_spec()
    # bad schema should be rejected by validated_copy
    with pytest.raises(QXtrlValidationError):
        spec.validated_copy(schema_version="qxtrl.el.ExperimentSpec/v9.9")
    # bad io should be rejected
    with pytest.raises(QXtrlValidationError):
        spec.validated_copy(io=NodeIOContract(consumes=(), produces=()))


def test_parameter_ref_validates_calibration_element_id():
    # standalone bad element id must be rejected (even without target context)
    with pytest.raises(QXtrlValidationError):
        ParameterProposalTarget(parameter_ref="calibration.BAD.xy.pi_amp", source_metric="pi_amp")
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref="calibration.BAD.xy.pi_amp", unit="a.u.", values=(0.1,))


def test_parameter_ref_restricts_pulse_roles_for_mvp():
    # unknown pulse role should be rejected for Rabi MVP
    with pytest.raises(QXtrlValidationError):
        ScanAxisSpec(axis_id="x", parameter_ref="pulse.foo.bar", unit="a.u.", values=(0.1,))
