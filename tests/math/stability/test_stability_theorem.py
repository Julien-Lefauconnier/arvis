# tests/math/stability/test_stability_theorem.py

from arvis.math.stability.theorem import is_globally_stable


def test_stability_theorem_true():
    cert = {
        "local": True,
        "global": True,
        "switching": True,
    }

    assert is_globally_stable(cert) is True


def test_stability_theorem_false():
    cert = {
        "local": True,
        "global": False,
        "switching": True,
    }

    assert is_globally_stable(cert) is False