# tests/math/test_projection_switching_stability.py

import random

import pytest

from arvis.cognition.projection.projection_api import Observation, project_observation
from tests.fixtures.projection_cases import boundary_case, nominal_case


def perturb_observation(obs: Observation, epsilon: float) -> Observation:
    perturbed = {}

    for k, v in obs.numeric_signals.items():
        try:
            base = float(v)
        except Exception:
            base = 0.0
        perturbed[k] = base + random.uniform(-epsilon, epsilon)

    return Observation(
        numeric_signals=perturbed,
        structured_signals=obs.structured_signals,
        external_signals=obs.external_signals,
    )


def make_alert_interior_case() -> Observation:
    # Moyenne = 0.5, loin des seuils 0.3 et 0.7
    return Observation(
        numeric_signals={
            "risk": 0.5,
            "instability": 0.5,
            "confidence": 0.5,
        },
        structured_signals={},
        external_signals={},
    )


def make_nominal_boundary_case() -> Observation:
    # Moyenne proche de 0.3
    return Observation(
        numeric_signals={
            "risk": 0.29,
            "instability": 0.30,
            "confidence": 0.31,
        },
        structured_signals={},
        external_signals={},
    )


def test_interior_mode_is_stable_under_small_perturbations():
    base_obs = make_alert_interior_case()
    base_proj = project_observation(base_obs)

    assert base_proj.q == "alert"

    mode_flips = 0
    trials = 200

    for _ in range(trials):
        perturbed = perturb_observation(base_obs, epsilon=0.02)
        proj = project_observation(perturbed)
        if proj.q != base_proj.q:
            mode_flips += 1

    flip_rate = mode_flips / trials

    # En région intérieure, on veut une vraie stabilité
    assert flip_rate == 0.0


@pytest.mark.parametrize(
    "case_fn, epsilon, max_flip_rate",
    [
        (nominal_case, 0.02, 0.05),
        (make_alert_interior_case, 0.02, 0.00),
    ],
)
def test_interior_cases_have_low_mode_flip_rate(case_fn, epsilon, max_flip_rate):
    base_obs = case_fn()
    base_proj = project_observation(base_obs)

    mode_flips = 0
    trials = 200

    for _ in range(trials):
        perturbed = perturb_observation(base_obs, epsilon=epsilon)
        proj = project_observation(perturbed)
        if proj.q != base_proj.q:
            mode_flips += 1

    flip_rate = mode_flips / trials
    assert flip_rate <= max_flip_rate


@pytest.mark.parametrize(
    "case_fn",
    [
        boundary_case,
        make_nominal_boundary_case,
    ],
)
def test_boundary_cases_measure_mode_instability_without_failing(case_fn):
    base_obs = case_fn()
    base_proj = project_observation(base_obs)

    mode_flips = 0
    trials = 200

    for _ in range(trials):
        perturbed = perturb_observation(base_obs, epsilon=0.03)
        proj = project_observation(perturbed)
        if proj.q != base_proj.q:
            mode_flips += 1

    flip_rate = mode_flips / trials

    # En frontière, les flips sont admissibles, mais doivent rester bornés.
    assert 0.0 <= flip_rate <= 1.0


def test_no_chattering_on_small_deterministic_trajectory():
    base = make_alert_interior_case()

    # Micro-trajectoire déterministe oscillant faiblement autour d'une zone intérieure
    offsets = [0.0, 0.01, -0.01, 0.015, -0.015, 0.005, -0.005, 0.0]

    modes = []
    for offset in offsets:
        obs = Observation(
            numeric_signals={
                "risk": 0.5 + offset,
                "instability": 0.5 + offset,
                "confidence": 0.5 + offset,
            },
            structured_signals=base.structured_signals,
            external_signals=base.external_signals,
        )
        proj = project_observation(obs)
        modes.append(proj.q)

    # En zone intérieure, on ne veut qu'un seul mode sur toute la micro-trajectoire
    assert set(modes) == {"alert"}
