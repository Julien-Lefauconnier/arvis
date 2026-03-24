# tests/api/test_ir_contract.py

import json

from arvis.api.ir import build_ir_view, IR_VERSION

def test_ir_has_required_fields(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert "version" in ir
    assert "fingerprint" in ir
    assert "input" in ir
    assert "context" in ir
    assert "decision" in ir
    assert "state" in ir
    assert "gate" in ir
    assert "meta" in ir


def test_ir_version_is_stable(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert ir["version"] == IR_VERSION
    assert isinstance(ir["version"], str)


def test_ir_is_deterministic(dummy_pipeline_result):
    ir1 = build_ir_view(dummy_pipeline_result)
    ir2 = build_ir_view(dummy_pipeline_result)

    assert ir1 == ir2


def test_ir_is_json_serializable(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    json.dumps(ir) 


def test_ir_no_private_fields(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    def check(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                assert not k.startswith("_")
                check(v)
        elif isinstance(obj, list):
            for v in obj:
                check(v)

    check(ir)


def test_ir_handles_none_fields():
    class Dummy:
        ir_input = None
        ir_context = None
        ir_decision = None
        ir_state = None
        ir_gate = None

    ir = build_ir_view(Dummy())

    assert ir["input"] is None
    assert ir["context"] is None
    assert ir["decision"] is None
    assert ir["state"] is None
    assert ir["gate"] is None


def test_ir_meta_is_always_present(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert "meta" in ir
    assert isinstance(ir["meta"], dict)


EXPECTED_KEYS = {
    "version",
    "fingerprint",
    "input",
    "context",
    "decision",
    "state",
    "gate",
    "meta",
}


def test_ir_top_level_keys_are_stable(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert set(ir.keys()) == EXPECTED_KEYS

def test_ir_version_is_exact_v1(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)
    assert ir["version"] == "arvis-ir.v1"


def test_ir_fingerprint_is_present_and_string(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)
    assert isinstance(ir["fingerprint"], str)
    assert ir["fingerprint"] != ""