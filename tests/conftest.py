# tests/conftest.py

import sys
from pathlib import Path

import pytest

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

# force pytest to use the local repo version of arvis
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def pipeline():
    return CognitivePipeline()


@pytest.fixture
def ctx():
    return CognitivePipelineContext(
        user_id="test-user", cognitive_input={"query": "test"}
    )


class DummyIR:
    def to_dict(self):
        return {"ok": True}


class DummyPipelineResult:
    ir_input = DummyIR()
    ir_context = DummyIR()
    ir_decision = DummyIR()
    ir_state = DummyIR()
    ir_gate = DummyIR()


@pytest.fixture
def dummy_pipeline_result():
    return DummyPipelineResult()


# ============================================================
# 🧪 Shared fixtures for Π / projection / gate tests
# ============================================================


@pytest.fixture
def minimal_ctx():
    """
    Minimal but realistic context for Π structured tests.
    Must stay ZKCS-safe and numeric.
    """
    return CognitivePipelineContext(
        user_id="test_user",
        cognitive_input=None,
        system_tension=0.4,
        drift_score=0.1,
        uncertainty=0.2,
        collapse_risk=0.3,
        regime="stable",
        switching_safe=True,
        delta_w=0.05,
    )


@pytest.fixture
def ctx_with_ir(minimal_ctx):
    """
    Context enriched with IR objects (used by Π structured + gate tests).
    """
    from arvis.ir.decision import CognitiveDecisionIR
    from arvis.ir.gate import CognitiveGateIR, CognitiveGateVerdictIR
    from arvis.ir.state import CognitiveRiskIR, CognitiveStateIR

    minimal_ctx.ir_decision = CognitiveDecisionIR(
        decision_id="d1",
        decision_kind="action",
        memory_intent="none",
    )

    minimal_ctx.ir_gate = CognitiveGateIR(
        verdict=CognitiveGateVerdictIR.ALLOW,
        bundle_id="b1",
        reason_codes=("ok",),
        risk_level=0.2,
    )

    minimal_ctx.ir_state = CognitiveStateIR(
        state_id="s1",
        bundle_id="b1",
        dv=0.1,
        collapse_risk=CognitiveRiskIR(
            mh_risk=0.1,
            world_risk=0.2,
            forecast_risk=0.3,
            fused_risk=0.3,
            smoothed_risk=0.25,
        ),
        epsilon=0.15,
        early_warning=False,
    )

    return minimal_ctx
