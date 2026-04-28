# tests/kernel/stages/test_projection_stage_pi_impl.py

from arvis.kernel.pipeline.stages.projection_stage import ProjectionStage
from arvis.kernel.projection.domain import NumericBounds, ProjectionDomain
from arvis.kernel.projection.pi_impl import PiImpl
from arvis.kernel.projection.validator import ProjectionValidator


class DummyCtx:
    def __init__(self) -> None:
        self.system_tension = 55.0
        self.conflict_pressure = 10.0
        self.coherence_score = 0.75
        self.control_signal = 20.0
        self.adaptive_kappa_eff = 0.2

        self.projected_state = None
        self.pi_state = None
        self.projection_view = None
        self.projection_certificate = None
        self.projection_domain_valid = None
        self.projection_margin = None
        self.extra = {}


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

    assert ctx.projected_state is not None
    assert ctx.pi_state is not None
    assert ctx.projection_view is not None
    assert ctx.projection_certificate is not None
    assert ctx.projection_domain_valid is True
    assert ctx.projection_margin is not None
    assert ctx.extra["projection_source"] == "PiImpl"
    assert ctx.extra["projection_structured"] is True
    assert ctx.extra["pi_structured_available"] is True
    assert ctx.extra["projection_semantics"] == "structured+certified"


def test_projection_stage_persists_structured_pi_state():
    ctx = DummyCtx()
    pipeline = DummyPipeline()
    stage = ProjectionStage()

    stage.run(pipeline, ctx)

    assert ctx.pi_state is not None
    assert ctx.pi_state.x is not None
    assert ctx.pi_state.z is not None
    assert ctx.pi_state.q is not None
    assert ctx.pi_state.w is not None
    assert ctx.pi_state.z.gate.verdict in {
        "allow",
        "require_confirmation",
        "abstain",
    }
