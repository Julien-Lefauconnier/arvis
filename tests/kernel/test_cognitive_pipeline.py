# tests/kernel/test_cognitive_pipeline.py

from datetime import datetime, timezone

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal
from arvis.timeline.timeline_entry import TimelineEntry, TimelineEntryNature
from arvis.timeline.timeline_types import TimelineEntryType
from arvis.cognition.confirmation.confirmation_result import (
    ConfirmationResult,
    ConfirmationStatus,
)
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus


# ---------------------------------------------------------
# Helpers / Mocks
# ---------------------------------------------------------


class DummyCoreModel:
    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.2
            drift_score = 0.1
            regime = "stable"
            stable = True
            prev_lyap = 0.5
            cur_lyap = 0.4

        return DummySnapshot()


class BlockingCoreModel:
    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.9
            drift_score = 1.0
            regime = "unstable"
            stable = False
            prev_lyap = 0.1
            cur_lyap = 1.0

        return DummySnapshot()


class NoRegimeCoreModel:
    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.1
            drift_score = 0.0
            regime = None
            stable = True
            prev_lyap = 0.5
            cur_lyap = 0.4

        return DummySnapshot()


class ConfirmationCoreModel:
    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.2
            drift_score = 0.1
            regime = "stable"
            stable = True
            prev_lyap = 0.2
            cur_lyap = 0.35

        return DummySnapshot()


def make_ctx():
    return CognitivePipelineContext(
        cognitive_input={},
        user_id="test_user",
        timeline=[],
        introspection=None,
        explanation=None,
    )


# ---------------------------------------------------------
# 1. Basic pipeline run
# ---------------------------------------------------------


def test_pipeline_runs_minimal():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.bundle is not None
    assert result.decision is not None
    assert result.control is not None


# ---------------------------------------------------------
# 2. Execution intent when ALLOW
# ---------------------------------------------------------


def test_pipeline_no_intent_when_abstain_even_if_confirmation_required():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.requires_confirmation is True
    assert result.gate_result == LyapunovVerdict.ABSTAIN
    assert result.executable_intent is None
    assert result.execution_status in {
        ExecutionGateStatus.BLOCKED_CONFIRMATION,
        ExecutionGateStatus.BLOCKED_ABSTAIN,
    }


# ---------------------------------------------------------
# 3. No intent when Lyapunov blocks
# ---------------------------------------------------------


def test_pipeline_blocks_execution_when_unstable():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=BlockingCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.gate_result is not None
    assert result.executable_intent is None


# ---------------------------------------------------------
# 4. Temporal layer impacts risk
# ---------------------------------------------------------


def test_temporal_layer_modulates_risk():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    ctx.timeline = [
        TimelineEntry(
            entry_id="entry-conflict-1",
            created_at=datetime.now(timezone.utc),
            type=TimelineEntryType.SYSTEM_NOTICE,
            title="Conflict notice",
            description="conflict detected",
            action_id=None,
            place_id=None,
            origin_ref=None,
            nature=TimelineEntryNature.EVENT,
            device_id="0" * 64,
            lamport=0,
        )
    ]

    result = pipeline.run(ctx)

    assert result.control.temporal_pressure is not None
    assert result.control.temporal_modulation is not None


# ---------------------------------------------------------
# 5. Epsilon is computed and positive
# ---------------------------------------------------------


def test_epsilon_is_positive():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.control.epsilon > 0


# ---------------------------------------------------------
# 6. Regime fallback works
# ---------------------------------------------------------


def test_regime_fallback_to_transition():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=NoRegimeCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.control.regime is not None


# ---------------------------------------------------------
# 7. Drift propagation
# ---------------------------------------------------------


def test_drift_is_propagated():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.control.drift is not None
    assert isinstance(ctx.drift_score, DriftSignal)


# ---------------------------------------------------------
# 8. Signals integration
# ---------------------------------------------------------


def test_pipeline_outputs_risk_signal():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    pipeline.run(ctx)

    assert isinstance(ctx.collapse_risk, RiskSignal)


def test_pipeline_outputs_uncertainty_signal():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    pipeline.run(ctx)

    assert isinstance(ctx.uncertainty, UncertaintySignal)


def test_pipeline_outputs_drift_signal():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    pipeline.run(ctx)

    assert isinstance(ctx.drift_score, DriftSignal)


# ---------------------------------------------------------
# 11. ActionDecision integration
# ---------------------------------------------------------


def test_pipeline_outputs_action_decision():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.action_decision is not None
    assert result.action_decision.allowed is False
    assert result.action_decision.requires_user_validation is True


def test_action_decision_blocks_when_unstable():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=BlockingCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.action_decision is not None
    assert result.action_decision.allowed is False
    assert result.action_decision.audit_required is True


def test_action_and_intent_consistency():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    if result.gate_result == LyapunovVerdict.ABSTAIN:
        assert result.executable_intent is None
    else:
        assert result.executable_intent is not None


# ---------------------------------------------------------
# 12. Confirmation integration
# ---------------------------------------------------------


def test_pipeline_generates_confirmation_request():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=ConfirmationCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.confirmation_request is not None
    assert result.execution_status == ExecutionGateStatus.BLOCKED_CONFIRMATION
    assert result.requires_confirmation is True
    assert result.can_execute is False


def test_confirmation_result_confirmed_allows_execution():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=ConfirmationCoreModel())

    ctx = make_ctx()
    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.CONFIRMED,
    )

    result = pipeline.run(ctx)

    assert result.gate_result == LyapunovVerdict.ALLOW
    assert result.executable_intent is not None
    assert result.can_execute is True
    assert result.requires_confirmation is False


def test_confirmation_result_rejected_blocks_execution():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=ConfirmationCoreModel())

    ctx = make_ctx()
    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.REJECTED,
    )

    result = pipeline.run(ctx)

    assert result.gate_result == LyapunovVerdict.ABSTAIN
    assert result.executable_intent is None
    assert result.execution_status == ExecutionGateStatus.BLOCKED_ABSTAIN


def test_no_confirmation_request_if_result_already_present():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=ConfirmationCoreModel())

    ctx = make_ctx()
    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.CONFIRMED,
    )

    result = pipeline.run(ctx)

    assert result.confirmation_request is None


def test_requires_confirmation_flag_consistency():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=ConfirmationCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.requires_confirmation is True
    assert result.can_execute is False


def test_requires_confirmation_false_after_resolution():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=ConfirmationCoreModel())

    ctx = make_ctx()
    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.CONFIRMED,
    )

    result = pipeline.run(ctx)

    assert result.requires_confirmation is False


def test_conflict_triggers_confirmation_even_if_stable():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    ctx.extra["conflict_pressure"] = 1.0

    result = pipeline.run(ctx)

    assert result.requires_confirmation is True


# ---------------------------------------------------------
# 13. trace integration
# ---------------------------------------------------------


def test_pipeline_produces_trace():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())

    ctx = CognitivePipelineContext(
        user_id="test_user",
        cognitive_input={"text": "hello"},
        timeline=[],
    )

    result = pipeline.run(ctx)

    assert result.trace is not None
    assert result.trace.user_id == ctx.user_id


# ---------------------------------------------------------
# 14. observability integration
# ---------------------------------------------------------


def test_observability_is_attached_to_pipeline():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.trace.predictive is not None
    assert result.trace.stability is not None
    assert result.trace.symbolic is not None


# ---------------------------------------------------------
# 15. Composite Lyapunov integration (ΔW behavior)
# ---------------------------------------------------------


class CompositePositiveDeltaCore:
    """
    Fast s'améliore légèrement, mais le slow state diverge fortement
    entre deux cycles -> ΔW > 0 au second run.
    """

    def __init__(self):
        self.step = 0

    def compute(self, bundle):
        self.step += 1

        if self.step == 1:

            class Snapshot:
                collapse_risk = 0.2
                drift_score = 0.05
                regime = "stable"
                stable = True
                prev_lyap = 0.30
                cur_lyap = 0.25
                reflexive_state = {
                    "stability_memory": 0.05,
                    "structural_risk": 0.05,
                    "regime_persistence": 0.05,
                    "uncertainty_drift": 0.05,
                }

            return Snapshot()

        class Snapshot:
            collapse_risk = 0.2
            drift_score = 0.05
            regime = "stable"
            stable = True
            prev_lyap = 0.25
            cur_lyap = 0.20
            reflexive_state = {
                "stability_memory": 0.90,
                "structural_risk": 0.90,
                "regime_persistence": 0.90,
                "uncertainty_drift": 0.90,
            }

        return Snapshot()


class CompositeNegativeDeltaCore:
    """
    Fast + slow s'améliorent → ΔW < 0
    """

    def compute(self, bundle):
        class Snapshot:
            collapse_risk = 0.2
            drift_score = 0.05
            regime = "stable"
            stable = True
            prev_lyap = 0.6
            cur_lyap = 0.2

            reflexive_state = {
                "stability_memory": 0.1,
                "structural_risk": 0.1,
                "regime_persistence": 0.1,
                "uncertainty_drift": 0.1,
            }

        return Snapshot()


def test_pipeline_blocks_when_delta_w_positive():
    """
    Cas critique :
    fast s'améliore légèrement MAIS slow diverge fortement
    entre t-1 et t -> ΔW > 0 -> DOIT bloquer
    """
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=CompositePositiveDeltaCore())

    ctx = make_ctx()
    ctx.extra["force_safe_projection"] = True
    ctx.extra["force_safe_switching"] = True
    ctx.switching_runtime = None
    ctx.switching_params = None

    ctx.global_stability_metrics = type(
        "M",
        (),
        {
            "ratio": 1.0,
            "kappa_violation": False,
        },
    )()

    ctx.projection_certificate = type(
        "P",
        (),
        {
            "domain_valid": True,
            "is_projection_safe": True,
            "margin_to_boundary": 1.0,
        },
    )()

    pipeline.run(ctx)  # initialise t0
    result = pipeline.run(ctx)

    assert ctx.delta_w is not None
    assert ctx.delta_w is not None
    print("verdict_transition_trace:", ctx.extra.get("verdict_transition_trace"))
    print("fusion_reasons:", ctx.extra.get("fusion_reasons"))
    print("kappa_hard_block:", ctx.extra.get("kappa_hard_block"))
    print("kappa_gap:", ctx.extra.get("kappa_gap"))
    print("adaptive_snapshot:", getattr(ctx, "adaptive_snapshot", None))
    print("validity_envelope:", getattr(ctx, "validity_envelope", None))
    print("projection_certificate:", getattr(ctx, "projection_certificate", None))
    assert result.gate_result in {
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    }
    assert result.requires_confirmation is True
    assert result.executable_intent is not None
    assert result.can_execute is False


def test_pipeline_allows_when_delta_w_negative():
    """
    Cas nominal :
    fast + slow s'améliorent → DOIT allow
    """
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=CompositeNegativeDeltaCore())

    ctx = make_ctx()
    ctx.extra["force_safe_projection"] = True
    ctx.extra["force_safe_switching"] = True
    # First pass (initialisation)
    ctx.switching_runtime = None
    ctx.switching_params = None

    ctx.global_stability_metrics = type(
        "M",
        (),
        {
            "ratio": 1.0,
            "kappa_violation": False,
        },
    )()

    ctx.projection_certificate = type(
        "P",
        (),
        {
            "domain_valid": True,
            "is_projection_safe": True,
            "margin_to_boundary": 1.0,
        },
    )()
    pipeline.run(ctx)

    # Second pass (ΔW calculable)
    result = pipeline.run(ctx)
    print("verdict_transition_trace:", ctx.extra.get("verdict_transition_trace"))
    print("fusion_reasons:", ctx.extra.get("fusion_reasons"))
    print("kappa_hard_block:", ctx.extra.get("kappa_hard_block"))
    print("kappa_gap:", ctx.extra.get("kappa_gap"))
    print("adaptive_snapshot:", getattr(ctx, "adaptive_snapshot", None))
    print("validity_envelope:", getattr(ctx, "validity_envelope", None))
    print("projection_certificate:", getattr(ctx, "projection_certificate", None))

    assert result.gate_result in {
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    }
    assert result.executable_intent is not None


def test_pipeline_handles_missing_slow_state():
    """
    Robustesse :
    pas de slow_state → pas de crash
    """

    class NoSlowCore:
        def compute(self, bundle):
            class Snapshot:
                collapse_risk = 0.2
                drift_score = 0.1
                regime = "stable"
                stable = True
                prev_lyap = 0.5
                cur_lyap = 0.4
                reflexive_state = None

            return Snapshot()

    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=NoSlowCore())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.gate_result is not None
    assert result.execution_status is not None


def test_pipeline_exposes_delta_w_in_context():
    """
    Vérifie que ΔW est bien exposé (debug / observability)
    """
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=CompositeNegativeDeltaCore())

    ctx = make_ctx()

    pipeline.run(ctx)  # t0 (init)
    pipeline.run(ctx)  # t1 (delta calculé)

    assert hasattr(ctx, "delta_w")
    assert ctx.delta_w is not None
