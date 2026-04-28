# tests/api/test_ir_canonical.py

from arvis.api.ir import build_ir_view
from arvis.api.ir_canonical import canonicalize_ir, hash_ir


def test_canonicalize_ir_is_deterministic(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    c1 = canonicalize_ir(ir)
    c2 = canonicalize_ir(ir)

    assert c1 == c2


def test_hash_ir_is_deterministic(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    h1 = hash_ir(ir)
    h2 = hash_ir(ir)

    assert h1 == h2


def test_hash_ir_changes_when_ir_changes(dummy_pipeline_result):
    ir1 = build_ir_view(dummy_pipeline_result)
    ir2 = build_ir_view(dummy_pipeline_result)

    ir2["meta"]["extra_test_flag"] = True

    assert hash_ir(ir1) != hash_ir(ir2)


def test_ir_contains_canonical_hash(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert "meta" in ir
    assert "canonical_hash" in ir["meta"]
    assert isinstance(ir["meta"]["canonical_hash"], str)
    assert len(ir["meta"]["canonical_hash"]) == 64
