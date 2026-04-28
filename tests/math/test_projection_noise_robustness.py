# tests/math/test_projection_noise_robustness.py

import math
import random

import pytest

from arvis.cognition.projection.projection_api import project_observation
from tests.fixtures.projection_cases import nominal_case


def add_noise(value: float, scale: float) -> float:
    return value + random.uniform(-scale, scale)


def noisy_observation(obs, noise_scale):
    perturbed = {}

    for k, v in obs.numeric_signals.items():
        try:
            base = float(v)
        except Exception:
            base = 0.0

        perturbed[k] = add_noise(base, noise_scale)

    return obs.__class__(
        numeric_signals=perturbed,
        structured_signals=obs.structured_signals,
        external_signals=obs.external_signals,
    )


def projection_norm(p):
    return sum(abs(v) for v in p.x + p.z + p.w)


@pytest.mark.parametrize("noise_scale", [0.01, 0.05, 0.1])
def test_projection_noise_robustness(noise_scale):
    base_obs = nominal_case()
    base_proj = project_observation(base_obs)

    drifts = []
    mode_flips = 0

    for _ in range(100):
        noisy = noisy_observation(base_obs, noise_scale)
        proj = project_observation(noisy)

        # drift measure
        drift = abs(projection_norm(proj) - projection_norm(base_proj))
        drifts.append(drift)

        # mode stability
        if proj.q != base_proj.q:
            mode_flips += 1

        # safety checks
        assert not math.isnan(projection_norm(proj))
        assert not math.isinf(projection_norm(proj))

    max_drift = max(drifts)
    p95 = sorted(drifts)[int(0.95 * len(drifts))]

    flip_rate = mode_flips / 100.0

    # -----------------------------
    # Assertions (initial thresholds)
    # -----------------------------

    # no explosion
    assert max_drift < 5.0

    # typical stability
    assert p95 < 2.0

    # switching stability (should be low for nominal region)
    assert flip_rate < 0.2
