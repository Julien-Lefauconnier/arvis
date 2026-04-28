# tests/api/test_os_ir_api.py

from __future__ import annotations

from arvis.api import CognitiveOS


def test_run_returns_result_view_with_ir_access() -> None:
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input={},
    )

    ir = result.to_ir()

    assert ir is not None
    assert ir["version"] == "arvis-ir.v1"
    assert "decision" in ir
    assert "state" in ir
    assert "gate" in ir


def test_run_ir_returns_machine_contract_dict() -> None:
    os = CognitiveOS()

    ir = os.run_ir(
        user_id="u1",
        cognitive_input={},
    )

    assert isinstance(ir, dict)
    assert ir["version"] == "arvis-ir.v1"
    assert "fingerprint" in ir
    assert "decision" in ir
    assert "state" in ir
    assert "gate" in ir


def test_run_ir_matches_result_view_to_ir() -> None:
    os = CognitiveOS()

    view = os.run(
        user_id="u1",
        cognitive_input={},
    )
    ir_from_view = view.to_ir()

    ir_direct = os.run_ir(
        user_id="u1",
        cognitive_input={},
    )

    assert ir_from_view == ir_direct


def test_to_dict_does_not_expose_internal_ir_field() -> None:
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input={},
    )

    data = result.to_dict()

    assert "ir" not in data
    assert "_ir" not in data


def test_run_without_trace_keeps_backward_compatible_output() -> None:
    os = CognitiveOS()
    os.config.enable_trace = False

    result = os.run(
        user_id="u1",
        cognitive_input={},
    )

    assert isinstance(result, dict)
    assert "action" in result
    assert "can_execute" in result
