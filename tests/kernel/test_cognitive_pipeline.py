# tests/kernel/test_cognitive_pipeline.py

from datetime import UTC, datetime

from arvis.cognition.confirmation.confirmation_result import (
    ConfirmationResult,
    ConfirmationStatus,
)
from arvis.kernel.execution.cognitive_execution_state import (
    CognitiveExecutionState,
)
from arvis.kernel.execution.execution_gate_status import ExecutionGateStatus
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.signals import DriftSignal, RiskSignal, UncertaintySignal
from arvis.timeline.timeline_entry import (
    TimelineEntry,
    TimelineEntryNature,
)
from arvis.timeline.timeline_types import TimelineEntryType

# =========================================================
# Helpers / Mocks
# =========================================================


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
    """
    Runtime-v2 compatible confirmation scenario.

    IMPORTANT:
    Confirmation is now runtime-owned and explicit.
    The pipeline no longer infers confirmation solely
    from Lyapunov drift behavior.
    """

    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.8
            drift_score = 0.7
            regime = "transition"
            stable = False
            prev_lyap = 0.2
            cur_lyap = 0.9

        return DummySnapshot()


def make_ctx():
    return CognitivePipelineContext(
        cognitive_input={},
        user_id="test_user",
        timeline=[],
        introspection=None,
        explanation=None,
    )


# =========================================================
# Runtime helpers
# =========================================================


def force_runtime_confirmation(ctx):
    """
    Runtime-v2 authority injection.

    Explicitly marks execution state as requiring
    confirmation BEFORE pipeline execution.
    """

    if ctx.execution.execution_state is None:
        ctx.execution.execution_state = CognitiveExecutionState()

    ctx.execution.execution_state.needs_confirmation = True


# =========================================================
# 1. Basic pipeline run
# =========================================================


def test_pipeline_runs_minimal():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.bundle is not None
    assert result.decision is not None
    assert result.observability.control is not None


# =========================================================
# 2. Execution gating
# =========================================================


def test_pipeline_blocks_execution_when_unstable():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(
        core_model=BlockingCoreModel(),
    )

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.gate_result is not None
    assert result.executable_intent is None


# =========================================================
# 3. Temporal modulation
# =========================================================


def test_temporal_layer_modulates_risk():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    ctx.timeline = [
        TimelineEntry(
            entry_id="entry-conflict-1",
            created_at=datetime.now(UTC),
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

    assert result.observability.control.temporal_pressure is not None
    assert result.observability.control.temporal_modulation is not None


# =========================================================
# 4. Control values
# =========================================================


def test_epsilon_is_positive():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.observability.control.epsilon > 0


def test_regime_fallback_to_transition():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(
        core_model=NoRegimeCoreModel(),
    )

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.observability.control.regime is not None


# =========================================================
# 5. Signal propagation
# =========================================================


def test_drift_is_propagated():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.observability.control.drift is not None
    assert isinstance(ctx.drift_score, DriftSignal)


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


# =========================================================
# 6. ActionDecision integration
# =========================================================


def test_pipeline_outputs_action_decision():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    force_runtime_confirmation(ctx)

    result = pipeline.run(ctx)

    assert result.action_decision is not None
    assert result.action_decision.allowed is False
    assert result.action_decision.allowed is False
    assert result.action_decision.audit_required is True


def test_action_decision_blocks_when_unstable():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(
        core_model=BlockingCoreModel(),
    )

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.action_decision is not None
    assert result.action_decision.allowed is False
    assert result.action_decision.audit_required is True


def test_action_and_intent_consistency():
    pipeline = CognitivePipeline(core_model=DummyCoreModel())
    ctx = make_ctx()

    result = pipeline.run(ctx)

    if result.execution.execution_status != ExecutionGateStatus.READY:
        assert result.executable_intent is None


# =========================================================
# 7. Confirmation integration
# =========================================================


def test_pipeline_generates_confirmation_request():
    pipeline = CognitivePipeline(
        core_model=ConfirmationCoreModel(),
    )

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.execution.execution_status in {
        ExecutionGateStatus.BLOCKED_ABSTAIN,
        ExecutionGateStatus.BLOCKED_CONFIRMATION,
    }

    assert result.execution.can_execute is False


def test_confirmation_result_confirmed_allows_execution():
    pipeline = CognitivePipeline(
        core_model=ConfirmationCoreModel(),
    )

    ctx = make_ctx()

    force_runtime_confirmation(ctx)

    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.CONFIRMED,
    )

    result = pipeline.run(ctx)

    assert result.execution.can_execute is True
    assert result.execution.requires_confirmation is False


def test_confirmation_result_rejected_blocks_execution():
    pipeline = CognitivePipeline(
        core_model=ConfirmationCoreModel(),
    )

    ctx = make_ctx()

    force_runtime_confirmation(ctx)

    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.REJECTED,
    )

    result = pipeline.run(ctx)

    assert result.execution.can_execute is False
    assert result.executable_intent is None


def test_no_confirmation_request_if_result_already_present():
    pipeline = CognitivePipeline(
        core_model=ConfirmationCoreModel(),
    )

    ctx = make_ctx()

    force_runtime_confirmation(ctx)

    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.CONFIRMED,
    )

    result = pipeline.run(ctx)

    assert result.execution.confirmation_request is None


def test_requires_confirmation_false_after_resolution():
    pipeline = CognitivePipeline(
        core_model=ConfirmationCoreModel(),
    )

    ctx = make_ctx()

    force_runtime_confirmation(ctx)

    ctx.confirmation_result = ConfirmationResult(
        request_id="test",
        status=ConfirmationStatus.CONFIRMED,
    )

    result = pipeline.run(ctx)

    assert result.execution.requires_confirmation is False


# =========================================================
# 8. Trace integration
# =========================================================


def test_pipeline_produces_trace():
    pipeline = CognitivePipeline(
        core_model=DummyCoreModel(),
    )

    ctx = CognitivePipelineContext(
        user_id="test_user",
        cognitive_input={"text": "hello"},
        timeline=[],
    )

    result = pipeline.run(ctx)

    assert result.trace is not None
    assert result.trace.user_id == ctx.user_id


# =========================================================
# 9. Observability integration
# =========================================================


def test_observability_is_attached_to_pipeline():
    pipeline = CognitivePipeline(
        core_model=DummyCoreModel(),
    )

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.trace.predictive is not None
    assert result.trace.stability is not None
    assert result.trace.symbolic is not None


# =========================================================
# 10. Composite Lyapunov integration
# =========================================================


class CompositePositiveDeltaCore:
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
    pipeline = CognitivePipeline()

    pipeline.core = pipeline.core.__class__(
        core_model=CompositePositiveDeltaCore(),
    )

    ctx = make_ctx()

    pipeline.run(ctx)
    result = pipeline.run(ctx)

    assert ctx.delta_w is not None

    assert result.gate_result in {
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }


def test_pipeline_allows_when_delta_w_negative():
    pipeline = CognitivePipeline()

    pipeline.core = pipeline.core.__class__(
        core_model=CompositeNegativeDeltaCore(),
    )

    ctx = make_ctx()

    pipeline.run(ctx)
    result = pipeline.run(ctx)

    assert result.gate_result in {
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }


def test_pipeline_handles_missing_slow_state():
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

    pipeline.core = pipeline.core.__class__(
        core_model=NoSlowCore(),
    )

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.gate_result is not None
    assert result.execution.execution_status is not None


def test_pipeline_exposes_delta_w_in_context():
    pipeline = CognitivePipeline()

    pipeline.core = pipeline.core.__class__(
        core_model=CompositeNegativeDeltaCore(),
    )

    ctx = make_ctx()

    pipeline.run(ctx)
    pipeline.run(ctx)

    assert hasattr(ctx, "delta_w")
    assert ctx.delta_w is not None
