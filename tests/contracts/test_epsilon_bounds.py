# tests/contracts/test_epsilon_bounds.py


from arvis.math.control.eps_adaptive import CognitiveMode, EpsAdaptiveParams
from arvis.math.control.irg_epsilon_controller import IRGEpsilonController


def test_epsilon_is_bounded():
    controller = IRGEpsilonController(EpsAdaptiveParams())

    for _ in range(50):
        eps = controller.compute(
            uncertainty=0.5,
            budget_used=0.5,
            delta_v=0.2,
            collapse_risk=0.3,
            latent_volatility=0.2,
            mode=CognitiveMode.NORMAL,
        )

        assert 0.0 <= eps <= 1.0
