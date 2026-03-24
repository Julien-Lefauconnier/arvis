# tests/integration/test_pipeline_ir_integration.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_pipeline_run_from_input_exports_ir(monkeypatch) -> None:
    pipeline = CognitivePipeline()

    decision_result = SimpleNamespace(
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

    monkeypatch.setattr(
        pipeline.decision,
        "evaluate",
        lambda ctx: decision_result,
    )

    monkeypatch.setattr(
        pipeline.passive_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.bundle_stage,
        "run",
        lambda _p, ctx: setattr(ctx, "bundle", SimpleNamespace(bundle_id="bundle-1")),
    )
    monkeypatch.setattr(
        pipeline.conflict_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.core_stage,
        "run",
        lambda _p, ctx: (
            setattr(ctx, "scientific_snapshot", SimpleNamespace()),
            setattr(ctx, "collapse_risk", 0.2),
            setattr(ctx, "drift_score", 0.1),
            setattr(ctx, "_dv", 0.1),
            setattr(ctx, "regime", "neutral"),
            setattr(ctx, "stable", True),
        ),
    )
    monkeypatch.setattr(
        pipeline.regime_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.temporal_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.conflict_modulation_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.control_stage,
        "run",
        lambda _p, ctx: (
            setattr(ctx, "control_snapshot", SimpleNamespace(epsilon=0.4, smoothed_risk=0.3)),
            setattr(ctx, "_epsilon", 0.4),
            setattr(ctx, "_effective_epsilon", 0.4),
        ),
    )
    monkeypatch.setattr(
        pipeline.gate_stage,
        "run",
        lambda _p, ctx: setattr(ctx, "gate_result", LyapunovVerdict.ALLOW),
    )
    monkeypatch.setattr(
        pipeline.control_feedback_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.structural_risk_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.confirmation_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.execution_stage,
        "run",
        lambda _p, ctx: (
            setattr(ctx, "_requires_confirmation", False),
            setattr(ctx, "_can_execute", True),
            setattr(ctx, "execution_status", "allow"),
        ),
    )
    monkeypatch.setattr(
        pipeline.action_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.intent_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.runtime_stage,
        "run",
        lambda _p, _ctx: None,
    )
    monkeypatch.setattr(
        pipeline.observability,
        "build",
        lambda ctx: {
            "predictive": SimpleNamespace(forecast_risk=0.12),
            "multi": SimpleNamespace(risk=0.15),
            "forecast": SimpleNamespace(world_risk=0.18),
            "stability": SimpleNamespace(fused_risk=0.21),
            "stats": None,
            "symbolic_state": None,
            "symbolic_drift": None,
            "symbolic_features": None,
        },
    )

    result = pipeline.run_from_input(
        {
            "user_id": "user-1",
            "session_id": "session-1",
            "cognitive_input": {
                "input_id": "input-1",
                "actor_id": "actor-1",
                "surface_kind": "linguistic",
                "intent_hint": "question",
            },
            "long_memory": {
                "constraints": ["no_share"],
                "preferences": {"language": "fr"},
            },
        }
    )

    assert result.ir_input is not None
    assert result.ir_input.input_id == "input-1"
    assert result.ir_input.surface_kind == "linguistic"

    assert result.ir_context is not None
    assert result.ir_context.user_id == "user-1"
    assert result.ir_context.session_id == "session-1"
    assert result.ir_context.long_memory_constraints == ("no_share",)
    assert result.ir_context.long_memory_preferences["language"] == "fr"

    assert result.ir_decision is not None
    assert result.ir_decision.decision_kind == "informational"
    assert result.ir_decision.reason_codes == ("informational_query",)

    assert result.ir_state is not None
    assert result.ir_state.bundle_id == "bundle-1"
    assert result.ir_state.epsilon == 0.4

    assert result.ir_gate is not None
    assert result.ir_gate.verdict.value == "allow"