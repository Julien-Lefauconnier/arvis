# tests/api/test_ir_view.py

from arvis.api.ir import build_ir_view
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline


def test_ir_view_is_present():
    pipeline = CognitivePipeline()

    result = pipeline.run_from_input(
        {
            "user_id": "u1",
            "cognitive_input": {},
        }
    )

    ir = build_ir_view(result)

    assert "input" in ir
    assert "context" in ir
    assert "decision" in ir
    assert "state" in ir
    assert "gate" in ir


def test_ir_view_is_serializable():
    pipeline = CognitivePipeline()

    result = pipeline.run_from_input(
        {
            "user_id": "u1",
            "cognitive_input": {},
        }
    )

    ir = build_ir_view(result)

    # doit être JSON-safe
    import json

    json.dumps(ir, default=str)


def test_os_exposes_ir_via_method():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})

    ir = result.to_ir()

    assert ir is not None
    assert isinstance(ir, dict)
    assert "version" in ir


def test_to_dict_does_not_expose_ir():
    from arvis.api import CognitiveOS

    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input={})

    data = result.to_dict()

    assert "ir" not in data  # backward compatibility
