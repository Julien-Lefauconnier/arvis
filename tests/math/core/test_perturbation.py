# tests/math/core/test_perturbation.py

from arvis.math.core.perturbation import compute_perturbation


class DummyCtx:
    uncertainty = 0.1
    drift_score = 0.2
    collapse_risk = 0.3
    symbolic_drift = 0.4


def test_perturbation_computation():
    ctx = DummyCtx()

    p = compute_perturbation(ctx)

    assert p is not None
    assert p.magnitude == 1.0  # 0.1+0.2+0.3+0.4
    assert p.uncertainty == 0.1
    assert p.drift == 0.2
    assert p.risk == 0.3
    assert p.symbolic == 0.4


def test_perturbation_zero():
    class Ctx:
        pass

    p = compute_perturbation(Ctx())

    assert p.magnitude == 0.0


def test_perturbation_significance():
    ctx = DummyCtx()
    p = compute_perturbation(ctx)

    assert p.is_significant(threshold=0.5) is True
