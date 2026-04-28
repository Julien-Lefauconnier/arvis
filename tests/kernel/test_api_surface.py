# tests/kernel/test_api_surface.py


def test_api_modules_importable():
    pass


def test_signals_are_importable():
    from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal

    r = RiskSignal(0.1)
    u = UncertaintySignal(0.2)
    d = DriftSignal(0.3)

    assert float(r) == 0.1
    assert float(u) == 0.2
    assert float(d) == 0.3
