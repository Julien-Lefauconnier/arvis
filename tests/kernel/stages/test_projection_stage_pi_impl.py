# tests/kernel/stages/test_projection_stage_pi_impl.py


from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.projection_stage import ProjectionStage
from arvis.kernel.projection.domain import NumericBounds, ProjectionDomain
from arvis.kernel.projection.pi_impl import PiImpl
from arvis.kernel.projection.validator import ProjectionValidator


def DummyCtx() -> CognitivePipelineContext:
    """Real pipeline context (campaign STRUCT, LOT S4)."""
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.observability.diagnostics.system_tension = 55.0
    ctx.conflict_pressure = 10.0
    ctx.coherence_score = 0.75
    ctx.control_signal = 20.0
    ctx.adaptive_kappa_eff = 0.2
    return ctx


class DummyPipeline:
    def __init__(self) -> None:
        self.pi_impl = PiImpl()
        self.projection_validator = ProjectionValidator(
            ProjectionDomain(
                bounds={
                    "state.system_tension": NumericBounds(0.0, 100.0),
                    "risk.conflict_pressure": NumericBounds(0.0, 100.0),
                    "state.coherence_score": NumericBounds(0.0, 1.0),
                    "control.control_signal": NumericBounds(0.0, 100.0),
                    "trace.adaptive_kappa_eff": NumericBounds(0.0, 1.0),
                }
            )
        )


def test_projection_stage_runs_pi_impl_and_certifies():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = ProjectionStage()

    stage.run(pipeline, ctx)

    assert ctx.projection.runtime_projection is not None
    assert ctx.projection.structured_projection is not None
    assert ctx.projection.view is not None
    assert ctx.projection.certificate is not None
    assert ctx.projection.domain_valid is True
    assert ctx.projection.margin is not None
    assert ctx.extra["projection_source"] == "PiImpl"
    assert ctx.extra["projection_structured"] is True
    assert ctx.extra["pi_structured_available"] is True
    assert ctx.extra["projection_semantics"] == "structured+certified"


def test_projection_stage_persists_structured_pi_state():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = ProjectionStage()

    stage.run(pipeline, ctx)

    assert ctx.projection.structured_projection is not None
    assert ctx.projection.structured_projection.x is not None
    assert ctx.projection.structured_projection.z is not None
    assert ctx.projection.structured_projection.q is not None
    assert ctx.projection.structured_projection.w is not None
    assert ctx.projection.structured_projection.z.gate.verdict in {
        "allow",
        "require_confirmation",
        "abstain",
    }
