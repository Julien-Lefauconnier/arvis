# tests/cognition/control/test_cognitive_control_engine_advanced.py


from arvis.cognition.control.cognitive_control_engine import (
    CognitiveControlEngine,
    CognitiveControlDeps,
)
from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


# -----------------------------
# Dummies
# -----------------------------

class DummyCore:
    def __init__(self):
        self.fused_risk = 0.6
        self.dv = 0.2
        self.world_prediction = type("WP", (), {
            "uncertainty": 0.7,
            "latent": [0.3],
        })()


class DummyBudget:
    def __init__(self):
        self.current_changes = 2
        self.max_changes = 10


# -----------------------------
# Temporal
# -----------------------------

class DummyPressure:
    def compute(self, user_id):
        return type("X", (), {"pressure": 1.0})()


class DummyRegulation:
    def compute(self, user_id):
        return type("X", (), {
            "risk_multiplier": 0.5,
            "epsilon_multiplier": 2.0,
        })()


def test_temporal_pressure_and_modulation():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            temporal_pressure=DummyPressure(),
            temporal_regulation=DummyRegulation(),
        )
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.temporal_pressure is not None
    assert result.temporal_modulation is not None
    assert result.epsilon > 0


# -----------------------------
# Hysteresis override
# -----------------------------

class DummyHysteresis:
    def update(self, user_id, risk):
        return "safe"


def test_mode_hysteresis_override():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(mode_hysteresis=DummyHysteresis())
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.gate_mode == "safe"


# -----------------------------
# Adaptive controller
# -----------------------------

class DummyAdaptive:
    def compute(self, **kwargs):
        return type("X", (), {"mode": "abstain"})()


def test_adaptive_controller_forces_abstain():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            adaptive_controller_factory=lambda user_id: DummyAdaptive()
        )
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.lyap_verdict == LyapunovVerdict.ABSTAIN


# -----------------------------
# Counterfactual
# -----------------------------

class DummyCF:
    def decide(self, **kwargs):
        return type("X", (), {"best_action": "confirm"})()


def test_counterfactual_confirm():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            counterfactual_factory=lambda: DummyCF()
        )
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.lyap_verdict in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }


# -----------------------------
# Bandit override
# -----------------------------

class DummyBandit:
    def recommend(self, current_risk):
        return "abstain"

    def update_from_risks(self, **kwargs):
        pass


def test_bandit_override():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            counterfactual_bandit_factory=lambda user_id: DummyBandit()
        )
    )

    runtime = CognitiveControlRuntime()
    runtime.last_action = "allow"
    runtime.last_risk = 0.8
    core = DummyCore()
    core.fused_risk = 1.0  # force high risk

    result = engine.compute(
        runtime=runtime,
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=core,
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=type("IRG", (), {"snapshot": lambda self: type("X", (), {"structural_risk": 0.0})()})(),
    )

    assert result.lyap_verdict == LyapunovVerdict.ABSTAIN


# -----------------------------
# Exploration + IRG scaling
# -----------------------------

class DummyExploration:
    def compute(self, **kwargs):
        return type("X", (), {"change_budget_scale": 0.5})()


def test_exploration_scales_budget():
    budget = DummyBudget()

    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            exploration_controller=DummyExploration()
        )
    )

    engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=budget,
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=type("IRG", (), {"snapshot": lambda self: type("X", (), {"structural_risk": 0.5})()})(),
    )

    assert budget.max_changes <= 10


# -----------------------------
# Drift / regime
# -----------------------------

class DummyStats:
    def push(self, *args):
        pass

    def snapshot(self, user_id):
        return type("X", (), {
            "samples": 50,
            "contraction_rate": 0.1,
            "instability_rate": 0.2,
        })()


class DummyDrift:
    def evaluate(self, **kwargs):
        return type("X", (), {"drift_score": 0.5})()


def test_drift_pipeline():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            stability_stats=DummyStats(),
            drift_detector_factory=lambda: DummyDrift(),
        )
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.drift is not None


# -----------------------------
# Local dynamics
# -----------------------------

class DummyDynamics:
    def push(self, **kwargs):
        pass


def test_local_dynamics():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            local_dynamics_factory=lambda: DummyDynamics()
        )
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result is not None


# -----------------------------
# Calibration
# -----------------------------

class DummyCalibration:
    def evaluate(self, _):
        return {"ok": True}


def test_calibration_path():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            calibration_engine=DummyCalibration(),
            stability_stats=DummyStats(),
            drift_detector_factory=lambda: DummyDrift(),
        )
    )

    result = engine.compute(
        runtime=CognitiveControlRuntime(),
        user_id="u",
        bundle=None,
        budget=DummyBudget(),
        core=DummyCore(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.calibration is not None