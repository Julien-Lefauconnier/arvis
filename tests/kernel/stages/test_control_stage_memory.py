# tests/kernel/stages/test_control_stage_memory.py

from arvis.kernel.pipeline.stages.control_stage import ControlStage
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.signals import DriftSignal, RiskSignal
from tests.fixtures.builders.context_builder import build_test_context


def test_memory_pressure_reduces_epsilon():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type(
            "R",
            (),
            {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()},
        )()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = build_test_context()
    ctx.user_id = "u1"
    ctx.scientific.core.collapse_risk = RiskSignal(0.1)
    ctx.scientific.core.drift_score = DriftSignal(0.1)
    ctx.scientific.regime_state.regime = "neutral"
    ctx.scientific.regime_state.stable = True
    ctx.timeline = []

    # 👉 memory pressure HIGH
    ctx.decision_layer = type("DL", (), {})()
    ctx.decision_layer.bundle = type(
        "B",
        (),
        {
            "memory_features": {
                "memory_pressure": 0.9,
                "has_constraints": False,
            }
        },
    )()

    stage.run(DummyPipeline(), ctx)

    assert ctx._effective_epsilon < 1.0
    assert ctx.memory_mode == "constrained"


def test_memory_constraints_reduce_epsilon():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type(
            "R",
            (),
            {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()},
        )()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = build_test_context()
    ctx.user_id = "u1"
    ctx.scientific.core.collapse_risk = RiskSignal(0.1)
    ctx.scientific.core.drift_score = DriftSignal(0.1)
    ctx.scientific.regime_state.regime = "neutral"
    ctx.scientific.regime_state.stable = True
    ctx.timeline = []
    ctx.decision_layer = type("DL", (), {})()
    ctx.decision_layer.bundle = type(
        "B",
        (),
        {
            "memory_features": {
                "memory_pressure": 0.0,
                "has_constraints": True,
            }
        },
    )()

    stage.run(DummyPipeline(), ctx)

    assert ctx.memory_constraints_active is True
    assert ctx._effective_epsilon < 1.0


def test_no_memory_features_safe_fallback():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type(
            "R",
            (),
            {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()},
        )()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = build_test_context()
    ctx.user_id = "u1"
    ctx.scientific.core.collapse_risk = RiskSignal(0.1)
    ctx.scientific.core.drift_score = DriftSignal(0.1)
    ctx.scientific.regime_state.regime = "neutral"
    ctx.scientific.regime_state.stable = True
    ctx.timeline = []
    ctx.decision_layer = type("DL", (), {})()
    ctx.decision_layer.bundle = None

    stage.run(DummyPipeline(), ctx)

    assert ctx.memory_mode is None or ctx.memory_mode == "free"


def test_memory_pressure_moderate_mode():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type(
            "R",
            (),
            {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()},
        )()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = build_test_context()
    ctx.user_id = "u1"
    ctx.scientific.core.collapse_risk = RiskSignal(0.1)
    ctx.scientific.core.drift_score = DriftSignal(0.1)
    ctx.scientific.regime_state.regime = "neutral"
    ctx.scientific.regime_state.stable = True
    ctx.timeline = []
    ctx.decision_layer = type("DL", (), {})()
    ctx.decision_layer.bundle = type(
        "B",
        (),
        {
            "memory_features": {
                "memory_pressure": 0.5,
                "has_constraints": False,
            }
        },
    )()

    stage.run(DummyPipeline(), ctx)

    assert ctx.memory_mode == "moderate"
