# tests/kernel/stages/test_pi_impl_llm_observation.py

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.projection.pi_impl import PiImpl


def DummyCtx() -> CognitivePipelineContext:
    """Real pipeline context (campaign STRUCT, LOT S4): the
    projection reads the canonical channels."""
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.observability.diagnostics.system_tension = 10.0
    ctx.conflict_pressure = 2.0
    ctx.coherence_score = 0.8
    ctx.control_signal = 1.0
    ctx.adaptive_kappa_eff = 0.1

    ctx.extra = {
        "llm_observation": {
            "entropy_mean": 0.9,
            "confidence_mean": 0.2,
            "logprob_variance": 0.1,
            "output_length": 42,
        }
    }
    return ctx


def test_pi_impl_includes_llm_observation():
    ctx = DummyCtx()
    pi = PiImpl()

    projected = pi.project(ctx)

    view = projected.to_projection_view()

    assert "risk.llm_variance" in view
    assert "trace.llm_output_length" in view


def test_pi_impl_injects_llm_signals():
    ctx = DummyCtx()
    pi = PiImpl()

    projected = pi.project(ctx)

    view = projected.to_projection_view()

    assert "trace.llm_entropy" in view
    assert "risk.llm_uncertainty" in view
    assert "state.llm_confidence" in view


def test_llm_entropy_impacts_uncertainty():
    ctx = DummyCtx()
    ctx.extra["llm_observation"]["entropy_mean"] = 0.95

    pi = PiImpl()
    state = pi.project_structured(ctx)

    assert state.x.uncertainty_mass >= 0.95


def test_llm_confidence_impacts_decision_commitment():
    ctx = DummyCtx()
    ctx.extra["llm_observation"]["confidence_mean"] = 0.9

    pi = PiImpl()
    state = pi.project_structured(ctx)

    assert state.x.decision_commitment >= 0.9


def test_llm_low_confidence_triggers_confirmation():
    ctx = DummyCtx()
    ctx.extra["llm_observation"]["confidence_mean"] = 0.1

    pi = PiImpl()
    state = pi.project_structured(ctx)

    assert state.z.gate.confirmation_required is True


def test_llm_latency_trace():
    ctx = DummyCtx()
    ctx.extra["llm_observation"]["latency_ms"] = 123

    pi = PiImpl()
    projected = pi.project(ctx)

    view = projected.to_projection_view()

    assert "trace.llm_latency" in view


def test_llm_evaluation_impacts_structured_uncertainty():
    ctx = DummyCtx()
    ctx.extra["llm_evaluation"] = {
        "confidence": 0.4,
        "uncertainty": 0.97,
        "variance": 0.1,
        "risk": 0.97,
    }

    state = PiImpl().project_structured(ctx)

    assert state.x.uncertainty_mass >= 0.97


def test_llm_evaluation_low_confidence_tightens_gate():
    ctx = DummyCtx()
    ctx.extra["llm_evaluation"] = {
        "confidence": 0.1,
        "uncertainty": 0.4,
        "variance": 0.1,
        "risk": 0.4,
    }

    state = PiImpl().project_structured(ctx)

    assert state.z.gate.confirmation_required is True


def test_llm_evaluation_risk_is_injected_into_w_state():
    ctx = DummyCtx()
    ctx.extra["llm_evaluation"] = {
        "confidence": 0.2,
        "uncertainty": 0.3,
        "variance": 0.1,
        "risk": 0.92,
    }

    state = PiImpl().project_structured(ctx)

    assert state.w.llm_risk_pressure >= 0.92
    assert state.w.uncertainty_pressure >= 0.92
    assert state.w.observation_gap >= 0.92


def test_low_llm_confidence_increases_w_risk_pressure():
    ctx = DummyCtx()
    ctx.extra["llm_observation"]["confidence_mean"] = 0.05

    state = PiImpl().project_structured(ctx)

    assert state.w.llm_risk_pressure >= 0.95
