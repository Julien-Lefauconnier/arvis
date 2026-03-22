# tests/fixtures/projection_cases.py

from arvis.cognition.projection.projection_api import Observation


def nominal_case() -> Observation:
    return Observation(
        numeric_signals={
            "risk": 0.2,
            "instability": 0.1,
            "confidence": 0.8,
        },
        structured_signals={},
        external_signals={},
    )


def high_risk_case() -> Observation:
    return Observation(
        numeric_signals={
            "risk": 0.9,
            "instability": 0.8,
            "confidence": 0.2,
        },
        structured_signals={},
        external_signals={},
    )


def boundary_case() -> Observation:
    return Observation(
        numeric_signals={
            "risk": 0.49,
            "instability": 0.51,
            "confidence": 0.5,
        },
        structured_signals={},
        external_signals={},
    )


def noisy_case() -> Observation:
    return Observation(
        numeric_signals={
            "risk": 0.2 + 0.01,
            "instability": 0.1 + 0.02,
            "confidence": 0.8 - 0.01,
        },
        structured_signals={},
        external_signals={},
    )


def invalid_case() -> Observation:
    return Observation(
        numeric_signals={
            "risk": "invalid",  # should trigger violation
        },
        structured_signals={},
        external_signals={},
    )