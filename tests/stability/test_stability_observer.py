# tests/stability/test_stability_observer.py

from arvis.stability.stability_observer import StabilityObserver


def test_stability_observer_importable():
    assert StabilityObserver is not None
