# tests/cognition/control/test_cognitive_control_engine_edges.py


from arvis.cognition.control.cognitive_control_engine import (
    CognitiveControlEngine,
    CognitiveControlDeps,
)
from arvis.cognition.control.cognitive_control_runtime import CognitiveControlRuntime
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.control.eps_adaptive import CognitiveMode


# --------------------------------------------------
# Dummy core variations
# --------------------------------------------------


class CoreWithMH:
    def __init__(self):
        self.fused_risk = 0.4
        self.dv = 0.1
        self.mh_snapshot = type("X", (), {"mode_hint": "safe"})()
        self.world_prediction = type(
            "WP",
            (),
            {
                "uncertainty": 0.6,
                "latent": [0.2],
            },
        )()


class CoreBroken:
    pass


class BudgetBroken:
    pass


# --------------------------------------------------
# Test 1 — prev_lyap path + CRITICAL mode
# --------------------------------------------------


class CriticalHysteresis:
    def update(self, user_id, risk):
        return CognitiveMode.CRITICAL


def test_prev_lyap_and_critical_mode():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(mode_hysteresis=CriticalHysteresis())
    )

    runtime = CognitiveControlRuntime()

    result = engine.compute(
        runtime=runtime,
        user_id="u",
        bundle=None,
        budget=type("B", (), {"current_changes": 1, "max_changes": 10})(),
        core=CoreWithMH(),
        prev_lyap=LyapunovState.from_scalar(0.1),
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=object(),
    )

    assert result.lyap_verdict == LyapunovVerdict.ABSTAIN


# --------------------------------------------------
# Test 2 — exception safety everywhere
# --------------------------------------------------


class Exploding:
    def compute(self, *a, **kw):
        raise RuntimeError("boom")

    def update(self, *a, **kw):
        raise RuntimeError("boom")

    def evaluate(self, *a, **kw):
        raise RuntimeError("boom")

    def push(self, *a, **kw):
        raise RuntimeError("boom")


def test_all_exceptions_are_safe():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            temporal_pressure=Exploding(),
            temporal_regulation=Exploding(),
            mode_hysteresis=Exploding(),
            inertia_controller=Exploding(),
            stability_stats=Exploding(),
            drift_detector_factory=lambda: Exploding(),
            regime_estimator_factory=lambda: Exploding(),
            regime_policy=Exploding(),
            exploration_controller=Exploding(),
            local_dynamics_factory=lambda: Exploding(),
            adaptive_controller_factory=lambda u: Exploding(),
            counterfactual_factory=lambda: Exploding(),
            counterfactual_bandit_factory=lambda u: Exploding(),
            calibration_engine=Exploding(),
        )
    )

    runtime = CognitiveControlRuntime()

    result = engine.compute(
        runtime=runtime,
        user_id="u",
        bundle=None,
        budget=BudgetBroken(),
        core=CoreBroken(),
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.1),
        irg=Exploding(),
    )

    assert result is not None
    assert 0.0 <= result.smoothed_risk <= 1.0


# --------------------------------------------------
# Test 3 — bandit confirm path + epsilon modulation fallback
# --------------------------------------------------


class ConfirmBandit:
    def recommend(self, current_risk):
        return "confirm"

    def update_from_risks(self, **kwargs):
        pass


class BadTemporal:
    def compute(self, user_id):
        return type(
            "X",
            (),
            {
                "risk_multiplier": "bad",  # will break to_float
                "epsilon_multiplier": "bad",
            },
        )()


def test_bandit_confirm_and_bad_temporal():
    engine = CognitiveControlEngine(
        deps=CognitiveControlDeps(
            counterfactual_bandit_factory=lambda u: ConfirmBandit(),
            temporal_regulation=BadTemporal(),
        )
    )

    runtime = CognitiveControlRuntime()

    core = type(
        "Core",
        (),
        {
            "fused_risk": 0.6,
            "dv": 0.1,
            "world_prediction": type(
                "WP",
                (),
                {
                    "uncertainty": 0.5,
                    "latent": [0.2],
                },
            )(),
        },
    )()

    budget = type("B", (), {"current_changes": 2, "max_changes": 10})()

    result = engine.compute(
        runtime=runtime,
        user_id="u",
        bundle=None,
        budget=budget,
        core=core,
        prev_lyap=None,
        cur_lyap=LyapunovState.from_scalar(0.2),
        irg=type("IRG", (), {"snapshot": lambda self: None})(),
    )

    assert result is not None
    assert result.lyap_verdict in {
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }
