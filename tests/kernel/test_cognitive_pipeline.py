# tests/kernel/test_cognitive_pipeline.py

import pytest
from datetime import datetime

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal
from arvis.timeline.timeline_entry import TimelineEntry, TimelineEntryNature
from arvis.timeline.timeline_types import TimelineEntryType
from datetime import datetime, timezone

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
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result is not None
    assert result.bundle is not None
    assert result.decision is not None
    assert result.control is not None


# ---------------------------------------------------------
# 2. Execution intent when ALLOW
# ---------------------------------------------------------

def test_pipeline_returns_executable_intent_when_allowed():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.executable_intent is not None
    assert result.executable_intent.user_id == "test_user"


# ---------------------------------------------------------
# 3. No intent when Lyapunov blocks
# ---------------------------------------------------------

class BlockingCoreModel:
    def compute(self, bundle):
        class DummySnapshot:
            collapse_risk = 0.9
            drift_score = 1.0
            regime = "unstable"
            stable = False
            prev_lyap = 0.1
            cur_lyap = 1.0  # strong increase → should block

        return DummySnapshot()


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
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    # Inject timeline with "conflict"
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
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert result.control.epsilon > 0


# ---------------------------------------------------------
# 6. Regime fallback works
# ---------------------------------------------------------

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
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert "score" in result.control.drift
    assert isinstance(ctx.drift_score, DriftSignal)


# ---------------------------------------------------------
# 8. Signals integration
# ---------------------------------------------------------

def test_pipeline_outputs_risk_signal():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    result = pipeline.run(ctx)

    assert isinstance(ctx.collapse_risk, RiskSignal)


# ---------------------------------------------------------
# 10. uncertaintySignal integration
# ---------------------------------------------------------

def test_pipeline_outputs_uncertainty_signal():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    pipeline.run(ctx)

    from arvis.math.signals import UncertaintySignal

    assert isinstance(ctx.uncertainty, UncertaintySignal)


# ---------------------------------------------------------
# 10. DriftSignal integration
# ---------------------------------------------------------

def test_pipeline_outputs_drift_signal():
    pipeline = CognitivePipeline()
    pipeline.core = pipeline.core.__class__(core_model=DummyCoreModel())

    ctx = make_ctx()

    pipeline.run(ctx)

    assert isinstance(ctx.drift_score, DriftSignal)