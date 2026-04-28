# tests/cognition/control/test_cognitive_control_engine.py


from arvis.cognition.control.cognitive_control_engine import (
    CognitiveControlEngine,
    CognitiveControlDeps,
)
from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.math.lyapunov.lyapunov import LyapunovState


# ---------------------------------------------------------------------
# BASE DUMMY
# ---------------------------------------------------------------------


class Dummy:
    pass


class DummyIRG:
    def snapshot(self):
        return type("X", (), {"structural_risk": 0.1})()


# ---------------------------------------------------------------------
# TEST 1 — MINIMAL RUN
# ---------------------------------------------------------------------


def test_control_engine_minimal_run():
    engine = CognitiveControlEngine(deps=CognitiveControlDeps())
    runtime = CognitiveControlRuntime()

    core = Dummy()
    core.fused_risk = 0.2
    core.dv = 0.1

    core.world_prediction = Dummy()
    core.world_prediction.uncertainty = 0.5
    core.world_prediction.latent = [0.1]

    budget = Dummy()
    budget.current_changes = 1
    budget.max_changes = 10

    result = engine.compute(
        runtime=runtime,
        user_id="user",
        bundle=None,
        budget=budget,
        core=core,
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=DummyIRG(),
    )

    assert result is not None
    assert 0.0 <= result.smoothed_risk <= 1.0
    assert isinstance(result.epsilon, float)
    assert result.lyap_verdict is not None


# ---------------------------------------------------------------------
# TEST 2 — TEMPORAL + HYSTERESIS
# ---------------------------------------------------------------------


class DummyPressure:
    def compute(self, user_id):
        return type("X", (), {"pressure": 0.5})()


class DummyRegulation:
    def compute(self, user_id):
        return type(
            "X",
            (),
            {
                "risk_multiplier": 0.8,
                "epsilon_multiplier": 1.2,
            },
        )()


class DummyHysteresis:
    def update(self, user_id, risk):
        return "safe"


def test_control_engine_with_temporal_and_hysteresis():
    deps = CognitiveControlDeps(
        temporal_pressure=DummyPressure(),
        temporal_regulation=DummyRegulation(),
        mode_hysteresis=DummyHysteresis(),
    )

    engine = CognitiveControlEngine(deps=deps)
    runtime = CognitiveControlRuntime()

    core = type(
        "Core",
        (),
        {
            "fused_risk": 0.3,
            "dv": 0.1,
            "world_prediction": type(
                "WP",
                (),
                {
                    "uncertainty": 0.4,
                    "latent": [0.2],
                },
            )(),
        },
    )()

    budget = type("B", (), {"current_changes": 2, "max_changes": 10})()

    result = engine.compute(
        runtime=runtime,
        user_id="user",
        bundle=None,
        budget=budget,
        core=core,
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=DummyIRG(),
    )

    assert result.temporal_pressure is not None
    assert result.temporal_modulation is not None
    assert 0.0 <= result.smoothed_risk <= 1.0


# ---------------------------------------------------------------------
# TEST 3 — INERTIA + COUNTERFACTUAL + BANDIT
# ---------------------------------------------------------------------


class DummyInertia:
    def update(self, user_id, collapse_risk):
        return type("X", (), {"smoothed_risk": 0.9})()


class DummyCounterfactual:
    def decide(self, **kwargs):
        return type("X", (), {"best_action": "abstain"})()


class DummyBandit:
    def recommend(self, current_risk):
        return "confirm"

    def update_from_risks(self, **kwargs):
        pass


def test_control_engine_decision_override_paths():
    deps = CognitiveControlDeps(
        inertia_controller=DummyInertia(),
        counterfactual_factory=lambda: DummyCounterfactual(),
        counterfactual_bandit_factory=lambda user_id: DummyBandit(),
    )

    engine = CognitiveControlEngine(deps=deps)
    runtime = CognitiveControlRuntime()

    core = type(
        "Core",
        (),
        {
            "fused_risk": 0.8,
            "dv": 0.2,
            "world_prediction": type(
                "WP",
                (),
                {
                    "uncertainty": 0.6,
                    "latent": [0.3],
                },
            )(),
        },
    )()

    budget = type("B", (), {"current_changes": 5, "max_changes": 10})()

    result = engine.compute(
        runtime=runtime,
        user_id="user",
        bundle=None,
        budget=budget,
        core=core,
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=DummyIRG(),
    )

    assert result is not None
    assert 0.0 <= result.smoothed_risk <= 1.0
    assert result.lyap_verdict is not None


def test_control_engine_safe_failures():
    engine = CognitiveControlEngine(deps=CognitiveControlDeps())
    runtime = CognitiveControlRuntime()

    class Broken:
        pass

    result = engine.compute(
        runtime=runtime,
        user_id="u",
        bundle=None,
        budget=Broken(),
        core=Broken(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.1),
        irg=Broken(),
    )

    assert result is not None
    assert 0.0 <= result.smoothed_risk <= 1.0
