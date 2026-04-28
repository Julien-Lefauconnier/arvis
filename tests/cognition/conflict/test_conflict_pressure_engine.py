# tests/cognition/conflict/test_conflict_pressure_engine.py

import pytest

from arvis.cognition.conflict.conflict_pressure_engine import (
    ConflictPressureEngine,
)


# -----------------------------
# Helpers
# -----------------------------


class Conflict:
    def __init__(self, score=0.0, type=None):
        self.score = score
        self.type = type


# -----------------------------
# Nominal
# -----------------------------


def test_empty_conflicts():
    engine = ConflictPressureEngine()
    result = engine.compute([])

    assert float(result.global_score) == 0.0
    assert float(result.epistemic) == 0.0
    assert float(result.decisional) == 0.0
    assert float(result.temporal) == 0.0
    assert float(result.ethical) == 0.0


def test_single_conflict_epistemic():
    engine = ConflictPressureEngine()
    result = engine.compute([Conflict(score=0.3, type="epistemic")])

    assert float(result.global_score) == 0.3
    assert float(result.epistemic) == 0.3
    assert float(result.decisional) == 0.0


def test_multiple_conflicts_accumulation():
    engine = ConflictPressureEngine()

    conflicts = [
        Conflict(score=0.2, type="epistemic"),
        Conflict(score=0.3, type="decision"),
        Conflict(score=0.1, type="temporal"),
    ]

    result = engine.compute(conflicts)

    assert float(result.global_score) == pytest.approx(0.6)
    assert float(result.epistemic) == 0.2
    assert float(result.decisional) == 0.3
    assert float(result.temporal) == 0.1


# -----------------------------
# Saturation
# -----------------------------


def test_global_saturation():
    engine = ConflictPressureEngine()

    conflicts = [
        Conflict(score=0.7),
        Conflict(score=0.6),
    ]

    result = engine.compute(conflicts)

    assert float(result.global_score) == 1.0  # capped


def test_type_saturation():
    engine = ConflictPressureEngine()

    conflicts = [
        Conflict(score=0.8, type="ethical"),
        Conflict(score=0.7, type="ethical"),
    ]

    result = engine.compute(conflicts)

    assert float(result.ethical) == 1.0


# -----------------------------
# Robustness (getattr paths)
# -----------------------------


def test_missing_score():
    class BadConflict:
        type = "epistemic"

    engine = ConflictPressureEngine()
    result = engine.compute([BadConflict()])

    assert float(result.global_score) == 0.0
    assert float(result.epistemic) == 0.0


def test_missing_type():
    class BadConflict:
        score = 0.5

    engine = ConflictPressureEngine()
    result = engine.compute([BadConflict()])

    assert float(result.global_score) == 0.5
    # not attributed
    assert float(result.epistemic) == 0.0


def test_none_values():
    engine = ConflictPressureEngine()

    conflicts = [
        Conflict(score=None, type="epistemic"),
        Conflict(score=0.4, type=None),
    ]

    result = engine.compute(conflicts)

    assert float(result.global_score) == 0.4


# -----------------------------
# from_scalar
# -----------------------------


def test_from_scalar():
    engine = ConflictPressureEngine()

    result = engine.from_scalar(0.7)

    assert float(result.global_score) == 0.7


def test_from_scalar_saturation():
    engine = ConflictPressureEngine()

    result = engine.from_scalar(2.0)

    assert float(result.global_score) == 1.0
