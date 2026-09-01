# tests/kernel/stages/test_decision_stage_retry_injection.py
"""Decision stage: normalization and the tool-retry override.

Campaign RELEASE (LOT R2). The stage normalizes any decision payload
into a DecisionResult carrying memory_influence (ZK-safe), and when
the runtime policy requests a tool retry it rebuilds the override
from the LAST tool result and payload; without prior results the
retry request is inert.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.decision_stage import DecisionStage


def _pipeline(raw_result: object) -> SimpleNamespace:
    return SimpleNamespace(
        decision=SimpleNamespace(evaluate=lambda ctx: raw_result),
        _get_control_runtime=lambda user_id: SimpleNamespace(user_id=user_id),
    )


def _ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(user_id="test", cognitive_input={})


def test_duck_results_are_normalized_with_memory_influence() -> None:
    ctx = _ctx()

    DecisionStage().run(_pipeline(SimpleNamespace(reason="quick")), ctx)

    result = ctx.decision_layer.decision_result
    assert result is not None
    assert result.reason == "quick"
    assert result.memory_influence == {}
    # the IR mirror of the decision is built alongside
    assert ctx.decision_layer.ir_decision is not None


def test_retry_request_rebuilds_the_override_from_the_last_tool() -> None:
    ctx = _ctx()
    ctx.runtime_policy.retry_requested = True
    ctx.tooling.tool_results = [
        SimpleNamespace(tool_name="first_tool"),
        SimpleNamespace(tool_name="last_tool"),
    ]
    ctx.tooling.tool_payloads = [
        {"payload": {"q": 1}},
        {"payload": {"q": 2}},
    ]

    DecisionStage().run(_pipeline(SimpleNamespace(reason="retry")), ctx)

    assert ctx.tooling.tool_feedback == {
        "tool_override": {"tool": "last_tool", "payload": {"q": 2}}
    }


def test_retry_request_without_prior_results_is_inert() -> None:
    ctx = _ctx()
    ctx.runtime_policy.retry_requested = True

    DecisionStage().run(_pipeline(SimpleNamespace(reason="retry")), ctx)

    assert ctx.tooling.tool_feedback is None
