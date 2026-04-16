# tests/kernel/stages/test_control_stage_memory.py

from arvis.kernel.pipeline.stages.control_stage import ControlStage
from arvis.math.control.eps_adaptive import CognitiveMode

def test_memory_pressure_reduces_epsilon():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type("R", (), {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()})()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = type("Ctx", (), {})()
    ctx.user_id = "u1"
    ctx.collapse_risk = 0.1
    ctx.drift_score = 0.1
    ctx.regime = "neutral"
    ctx.stable = True
    ctx.timeline = []

    # 👉 memory pressure HIGH
    ctx.bundle = type("B", (), {
        "memory_features": {
            "memory_pressure": 0.9,
            "has_constraints": False,
        }
    })()

    stage.run(DummyPipeline(), ctx)

    assert ctx._effective_epsilon < 1.0
    assert ctx.memory_mode == "constrained"


def test_memory_constraints_reduce_epsilon():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type("R", (), {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()})()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = type("Ctx", (), {})()
    ctx.user_id = "u1"
    ctx.collapse_risk = 0.1
    ctx.drift_score = 0.1
    ctx.regime = "neutral"
    ctx.stable = True
    ctx.timeline = []

    ctx.bundle = type("B", (), {
        "memory_features": {
            "memory_pressure": 0.0,
            "has_constraints": True,
        }
    })()

    stage.run(DummyPipeline(), ctx)

    assert ctx.memory_constraints_active is True
    assert ctx._effective_epsilon < 1.0


def test_no_memory_features_safe_fallback():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type("R", (), {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()})()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = type("Ctx", (), {})()
    ctx.user_id = "u1"
    ctx.collapse_risk = 0.1
    ctx.drift_score = 0.1
    ctx.regime = "neutral"
    ctx.stable = True
    ctx.timeline = []
    ctx.bundle = None

    stage.run(DummyPipeline(), ctx)

    assert ctx.memory_mode is None or ctx.memory_mode == "free"


def test_memory_pressure_moderate_mode():
    stage = ControlStage()

    class DummyPipeline:
        hysteresis = type("H", (), {"update": lambda *a, **k: CognitiveMode.NORMAL})()
        epsilon_controller = type("E", (), {"compute": lambda *a, **k: 1.0})()
        regime_policy = type("R", (), {"compute": lambda *a, **k: type("X", (), {"epsilon_multiplier": 1.0})()})()
        exploration = type("X", (), {"compute": lambda *a, **k: None})()

    ctx = type("Ctx", (), {})()
    ctx.user_id = "u1"
    ctx.collapse_risk = 0.1
    ctx.drift_score = 0.1
    ctx.regime = "neutral"
    ctx.stable = True
    ctx.timeline = []

    ctx.bundle = type("B", (), {
        "memory_features": {
            "memory_pressure": 0.5,
            "has_constraints": False,
        }
    })()

    stage.run(DummyPipeline(), ctx)

    assert ctx.memory_mode == "moderate"


