# tests/kernel/stages/test_decision_stage_ir.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.decision_stage import DecisionStage


def test_decision_stage_populates_ir_decision() -> None:
    result = SimpleNamespace(
        memory_intent="none",
        proposed_actions=[],
        reason="informational_query",
        knowledge_snapshot=None,
        conflicts=[],
        gaps=[],
        reasoning_intents=[],
        uncertainty_frames=[],
        context_hints={},
    )

    pipeline = SimpleNamespace(
        decision=SimpleNamespace(evaluate=lambda ctx: result),
        _get_control_runtime=lambda user_id: "runtime-for-" + user_id,
    )

    ctx = SimpleNamespace(
        user_id="user-1",
        extra={},
    )

    stage = DecisionStage()
    stage.run(pipeline, ctx)

    assert ctx.decision_result is result
    assert ctx.ir_decision is not None
    assert ctx.ir_decision.decision_kind == "informational"
    assert ctx.control_runtime == "runtime-for-user-1"