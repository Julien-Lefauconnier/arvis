# test/math/confidence/test_system_confidence.py

from arvis.math.confidence.system_confidence import (
    SystemConfidenceInputs,
    compute_system_confidence,
)


def test_system_confidence_is_bounded():
    score = compute_system_confidence(
        SystemConfidenceInputs(
            delta_w=0.1,
            global_safe=True,
            switching_safe=True,
            has_history=True,
            has_observability=True,
            collapse_risk=0.2,
        )
    )

    assert 0.0 <= score <= 1.0


def test_system_confidence_decreases_under_instability():
    stable = compute_system_confidence(
        SystemConfidenceInputs(
            delta_w=-0.2,
            global_safe=True,
            switching_safe=True,
            has_history=True,
            has_observability=True,
            collapse_risk=0.1,
        )
    )

    unstable = compute_system_confidence(
        SystemConfidenceInputs(
            delta_w=3.0,
            global_safe=False,
            switching_safe=False,
            has_history=True,
            has_observability=True,
            collapse_risk=0.8,
        )
    )

    assert unstable < stable


def test_system_confidence_penalizes_missing_history_and_observability():
    full = compute_system_confidence(
        SystemConfidenceInputs(
            delta_w=0.0,
            global_safe=True,
            switching_safe=True,
            has_history=True,
            has_observability=True,
            collapse_risk=0.0,
        )
    )

    partial = compute_system_confidence(
        SystemConfidenceInputs(
            delta_w=None,
            global_safe=True,
            switching_safe=True,
            has_history=False,
            has_observability=False,
            collapse_risk=0.0,
        )
    )

    assert partial < full
