# tests/api/test_ir_llm_readability.py

from arvis.api.ir import build_ir_view


def test_ir_is_llm_readable(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    # règles simples mais puissantes
    assert isinstance(ir["decision"], dict)
    assert isinstance(ir["state"], dict)
    assert isinstance(ir["gate"], dict) or ir["gate"] is None

    # pas de types exotiques
    def check(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                check(v)
        elif isinstance(obj, list):
            for v in obj:
                check(v)
        else:
            assert isinstance(obj, (str, int, float, bool, type(None)))

    check(ir)


def test_ir_top_level_blocks_are_llm_readable(dummy_pipeline_result):
    ir = build_ir_view(dummy_pipeline_result)

    assert isinstance(ir["meta"], dict)
    assert ir["input"] is None or isinstance(ir["input"], dict)
    assert ir["context"] is None or isinstance(ir["context"], dict)
    assert ir["decision"] is None or isinstance(ir["decision"], dict)
    assert ir["state"] is None or isinstance(ir["state"], dict)
    assert ir["gate"] is None or isinstance(ir["gate"], dict)
