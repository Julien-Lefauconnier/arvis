# tests/tools/test_tool_retry.py

from arvis.api.os import CognitiveOS
from arvis.tools.base import BaseTool


def test_tool_retry_flow():

    calls = {"count": 0}

    class FailingThenSuccessTool(BaseTool):
        name = "retry_tool"

        def execute(self, input_data):
            calls["count"] += 1

            # first call fails
            if calls["count"] == 1:
                raise Exception("fail")

            # second call succeeds
            return {"ok": True}

    os = CognitiveOS()
    os.register_tool(FailingThenSuccessTool())

    # -------------------------
    # RUN 1 → fail
    # -------------------------
    ctx_extra = {}
    ctx_extra["force_tool"] = "retry_tool"

    os.run(
        user_id="u1",
        cognitive_input={"tool": "retry_tool"},
        extra=ctx_extra,
    )
    # check failure stored
    tool_results = ctx_extra.get("tool_results", [])
    assert len(tool_results) == 1
    assert tool_results[0].success is False

    # -------------------------
    # PREPARE RETRY
    # -------------------------
    next_extra = {
        "tool_results": tool_results,
        "tool_payloads": ctx_extra.get("tool_payloads", []),
        "retry_tool": True,
    }

    # -------------------------
    # RUN 2 → retry should succeed
    # -------------------------
    os.run(
        user_id="u1",
        cognitive_input={},
        extra=next_extra,
    )

    tool_results_2 = next_extra.get("tool_results", [])

    # now we should have 2 results
    assert len(tool_results_2) == 2

    # second call success
    assert tool_results_2[-1].success is True
    assert tool_results_2[-1].output["ok"] is True

    # ensure tool was actually retried
    assert calls["count"] == 2

    assert tool_results_2[-1].tool_name == "retry_tool"