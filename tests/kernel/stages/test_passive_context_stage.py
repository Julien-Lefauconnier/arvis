# tests/kernel/pipeline/stages/test_passive_context_stage.py

from arvis.kernel.pipeline.stages.passive_context_stage import PassiveContextStage


class DummyCtx:
    def __init__(self):
        self.extra = None
        self.conversation_context = None
        self.decision_result = None


class DummyPipeline:
    pass


def test_extra_is_initialized():
    stage = PassiveContextStage()
    ctx = DummyCtx()
    pipeline = DummyPipeline()

    stage.run(pipeline, ctx)

    assert isinstance(ctx.extra, dict)