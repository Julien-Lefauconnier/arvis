# tests/kernel/stages/test_decision_stage_memory.py

from arvis.kernel.pipeline.stages.decision_stage import DecisionStage
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.cognition.decision.decision_result import DecisionResult


class DummyPipeline:
    def __init__(self):
        class DummyDecision:
            def evaluate(self, ctx):
                return DecisionResult(reason="test")
        self.decision = DummyDecision()

    def _get_control_runtime(self, user_id):
        return None


def test_decision_stage_injects_memory_influence_default():
    pipeline = DummyPipeline()
    ctx = CognitivePipelineContext(user_id="u1", cognitive_input={})

    stage = DecisionStage()
    stage.run(pipeline, ctx)

    assert ctx.decision_result is not None
    assert hasattr(ctx.decision_result, "memory_influence")
    assert ctx.decision_result.memory_influence == {}


def test_decision_stage_preserves_memory_influence():
    class DummyDecision:
        def evaluate(self, ctx):
            return DecisionResult(
                reason="test",
                memory_influence={"memory_present": True}
            )

    pipeline = DummyPipeline()
    pipeline.decision = DummyDecision()

    ctx = CognitivePipelineContext(user_id="u1", cognitive_input={})

    stage = DecisionStage()
    stage.run(pipeline, ctx)

    assert ctx.decision_result.memory_influence["memory_present"] is True


def test_decision_stage_retry_does_not_drop_memory_influence():
    class DummyDecision:
        def evaluate(self, ctx):
            return DecisionResult(
                reason="test",
                memory_influence={"memory_pressure": 1.0}
            )

    pipeline = DummyPipeline()
    pipeline.decision = DummyDecision()

    ctx = CognitivePipelineContext(user_id="u1", cognitive_input={})
    ctx.extra["retry_tool"] = True
    ctx.extra["tool_results"] = [type("T", (), {"tool_name": "tool_x"})()]
    ctx.extra["tool_payloads"] = [{"payload": {"x": 1}}]

    stage = DecisionStage()
    stage.run(pipeline, ctx)

    assert ctx.decision_result.memory_influence["memory_pressure"] == 1.0