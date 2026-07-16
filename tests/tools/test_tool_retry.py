# tests/tools/test_tool_retry.py

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.runtime_controls import TrustedRuntimeControls
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
            if calls["count"] == 1:
                raise Exception("fail")
            return {"ok": True}

    os = CognitiveOS(
        CognitiveOSConfig(
            runtime_controls=TrustedRuntimeControls(
                force_tool="retry_tool",
                force_execution=True,
            )
        )
    )
    os.register_tool(FailingThenSuccessTool())

    result = os.run(
        user_id="u1",
        cognitive_input={
            "tool": "retry_tool",
            "spec": {"name": "retry_tool"},
        },
    )

    assert result.execution_view is not None

    # ---------------------------------------------------------
    # Public execution observability
    # ---------------------------------------------------------

    execution_view = result.execution_view

    # retry must emit TWO syscall executions
    assert execution_view.syscall_count == 2

    # tool failures are not yet projected into
    # execution_state.errors (runtime ownership model)
    assert execution_view.error_count == 0

    # retry path executed
    assert calls["count"] == 2

    # execution finalized correctly
    assert execution_view.execution_status is not None

    # retry policy observability
    runtime_policy = getattr(result.trace, "runtime_policy", None)

    if runtime_policy is not None:
        assert runtime_policy.retry_requested is True
        assert runtime_policy.retry_count == 1
