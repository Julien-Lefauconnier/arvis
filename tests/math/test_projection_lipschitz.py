# tests/math/test_projection_lipschitz.py

import math
import random


from arvis.cognition.projection.projection_api import project_observation, Observation
from tests.fixtures.projection_cases import nominal_case


# -----------------------------
# Helpers
# -----------------------------


def observation_distance(o1: Observation, o2: Observation) -> float:
    keys = set(o1.numeric_signals.keys()) | set(o2.numeric_signals.keys())

    total = 0.0
    for k in keys:
        v1 = o1.numeric_signals.get(k, 0.0)
        v2 = o2.numeric_signals.get(k, 0.0)

        try:
            v1 = float(v1)
            v2 = float(v2)
        except Exception:
            continue

        total += (v1 - v2) ** 2

    return math.sqrt(total)


def projection_distance(p1, p2) -> float:
    total = 0.0

    for v1, v2 in zip(p1.x, p2.x):
        total += (v1 - v2) ** 2

    for v1, v2 in zip(p1.z, p2.z):
        total += (v1 - v2) ** 2

    for v1, v2 in zip(p1.w, p2.w):
        total += (v1 - v2) ** 2

    # penalize mode changes (discontinuity)
    if p1.q != p2.q:
        total += 1.0

    return math.sqrt(total)


def perturb_observation(obs: Observation, epsilon: float) -> Observation:
    perturbed = {}

    for k, v in obs.numeric_signals.items():
        try:
            base = float(v)
        except Exception:
            base = 0.0

        noise = random.uniform(-epsilon, epsilon)
        perturbed[k] = base + noise

    return Observation(
        numeric_signals=perturbed,
        structured_signals=obs.structured_signals,
        external_signals=obs.external_signals,
    )


# -----------------------------
# Test
# -----------------------------


def test_projection_local_lipschitz():
    base_obs = nominal_case()
    base_proj = project_observation(base_obs)

    epsilons = [1e-3, 1e-2, 5e-2]
    ratios = []

    for eps in epsilons:
        for _ in range(50):
            perturbed = perturb_observation(base_obs, eps)

            proj = project_observation(perturbed)

            d_obs = observation_distance(base_obs, perturbed)
            d_proj = projection_distance(base_proj, proj)

            if d_obs > 1e-12:
                ratio = d_proj / d_obs
                ratios.append(ratio)

    assert len(ratios) > 0

    max_ratio = max(ratios)
    p95 = sorted(ratios)[int(0.95 * len(ratios))]

    # -----------------------------
    # Assertions (provisional thresholds)
    # -----------------------------

    assert not math.isinf(max_ratio)
    assert not math.isnan(max_ratio)

    # No explosion
    assert max_ratio < 100.0

    # Typical behavior bounded
    assert p95 < 25.0
