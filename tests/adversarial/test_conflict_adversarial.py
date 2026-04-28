# tests/adversarial/test_conflict_adversarial.py

from arvis.cognition.conflict.conflict_pressure_engine import ConflictPressureEngine


class Fake:
    def __init__(self, score, type):
        self.score = score
        self.type = type


def test_conflict_overflow():
    engine = ConflictPressureEngine()

    conflicts = [Fake(1000.0, "epistemic") for _ in range(1000)]

    result = engine.compute(conflicts)

    # saturation obligatoire
    assert result.global_score <= 1.0
    assert result.epistemic <= 1.0


def test_conflict_negative_values():
    engine = ConflictPressureEngine()

    conflicts = [Fake(-10.0, "ethical")]

    result = engine.compute(conflicts)

    # le système ne doit pas diverger
    assert result.global_score >= 0.0
