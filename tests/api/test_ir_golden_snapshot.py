# tests/api/test_ir_golden_snapshot.py

from arvis.api.ir import build_ir_view


def test_ir_golden_snapshot(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    # on enlève le hash pour comparaison stable
    ir_without_hash = dict(ir)
    ir_without_hash["meta"] = {}

    expected = {
        "version": "arvis-ir.v1",
        "fingerprint": "stable",
        "input": {},
        "context": {},
        "decision": {},
        "state": {},
        "gate": {},
        "meta": {},
    }

    assert ir_without_hash == expected

    # check séparé du hash
    assert "canonical_hash" in ir["meta"]


def test_ir_golden_snapshot_keys_are_exact(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert list(ir.keys()) == [
        "version",
        "fingerprint",
        "input",
        "context",
        "decision",
        "state",
        "gate",
        "meta",
    ]