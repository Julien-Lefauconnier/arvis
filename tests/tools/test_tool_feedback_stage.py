# tests/tools/test_tool_feedback_stage.py

from arvis.api.os import CognitiveOS
from arvis.tools.base import BaseTool


def test_tool_feedback_propagates_to_next_cycle():
    class DummyTool(BaseTool):
        name = "dummy"

        def execute(self, input_data):
            return {"ok": True}

    os = CognitiveOS()
    os.register_tool(DummyTool())

    # 🔥 inject directly tool_results (skip pipeline constraints)
    next_extra = {"tool_results": [{"tool": "dummy", "result": {"ok": True}}]}

    # RUN → feedback stage
    os.run(
        user_id="u1",
        cognitive_input={},
        extra=next_extra,
    )

    # ✅ ASSERTION
    assert "tool_feedback" in next_extra
    assert next_extra["tool_feedback"]["success"] is True
