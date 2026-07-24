# tests/math/test_linear_two_regime_example.py

"""The linear two-regime example of ARVIS_STABILITY_CORE_SPECIFICATIONS.

The specification document states that, for the exact system below,
simulations show decay of the composite energy and bounded trajectories
under switching (condition T1). A stated simulation must exist (a15
doctrine): this test executes that exact system, fixed seed, and pins
the claim.
"""

import random

import numpy as np

_RNG = random.Random(20260724)

A1 = np.array([[0.8, 0.1], [0.0, 0.7]])
A2 = np.array([[0.75, -0.1], [0.05, 0.8]])
B = np.array([0.1, 0.1])
K = np.array([0.2, 0.1])
ETA = 0.05
NOISE_BOUND = 0.05
DWELL = 5
STEPS = 400


def _composite_energy(x: np.ndarray, z: float) -> float:
    return float(x @ x + z * z)


def test_composite_energy_decays_and_trajectories_stay_bounded() -> None:
    x = np.array([1.0, -1.0])
    z = 1.0
    energies = []
    for step in range(STEPS):
        regime = A1 if (step // DWELL) % 2 == 0 else A2
        noise = np.array(
            [
                _RNG.uniform(-NOISE_BOUND, NOISE_BOUND),
                _RNG.uniform(-NOISE_BOUND, NOISE_BOUND),
            ]
        )
        x = regime @ x + B * z + noise
        z = (1.0 - ETA) * z + ETA * float(K @ x)
        energies.append(_composite_energy(x, z))

    initial = _composite_energy(np.array([1.0, -1.0]), 1.0)
    tail = energies[-100:]

    # Decay: the residual tube is far below the initial energy.
    assert max(tail) < initial / 10
    # Boundedness under switching: no excursion anywhere on the run.
    assert max(energies) < 10 * initial
