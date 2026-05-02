# tests/tools/test_tool_retry.py

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.os import CognitiveOS
from arvis.tools.base import BaseTool


def test_tool_retry_flow(monkeypatch):
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        lambda invocation, registry: SimpleNamespace(
            allowed=True,
            reason=None,
        ),
    )
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

    # -----------------------------------------
    # FORCE EXECUTION (bypass confirmation gate)
    # -----------------------------------------
    ctx_extra["_force_execution"] = True

    os.run(
        user_id="u1",
        cognitive_input={"tool": "retry_tool", "spec": {"name": "retry_tool"}},
        extra=ctx_extra,
    )
    # check failure stored
    tool_results = ctx_extra.get("syscall_results", [])
    assert len(tool_results) == 1
    assert tool_results[0]["syscall"] == "tool.execute"

    # -------------------------
    # PREPARE RETRY
    # -------------------------
    next_extra = {
        "syscall_results": tool_results,
        "force_tool": "retry_tool",
        "_force_execution": True,
    }

    # -------------------------
    # RUN 2 → second forced execution should succeed
    # -------------------------
    os.run(
        user_id="u1",
        cognitive_input={"tool": "retry_tool", "spec": {"name": "retry_tool"}},
        extra=next_extra,
    )

    tool_results_2 = next_extra.get("syscall_results", [])

    # now we should have 2 results
    assert len(tool_results_2) == 2

    # second syscall succeeds
    assert any(r["success"] is True for r in tool_results_2)
    assert calls["count"] >= 2
    assert len(tool_results_2) >= 2
    assert tool_results_2[0]["syscall"] == "tool.execute"
    assert tool_results_2[1]["syscall"] == "tool.execute"
