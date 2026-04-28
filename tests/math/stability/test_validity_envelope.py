# tests/math/stability/test_validity_envelope.py

from arvis.math.stability.validity_envelope import build_validity_envelope


def test_validity_envelope_valid_case():
    env = build_validity_envelope(
        projection_available=True,
        switching_safe=True,
        exponential_safe=True,
        kappa_safe=True,
        adaptive_available=True,
        adaptive_band="stable",
    )
    assert env.valid is True
    assert env.reason is None


def test_validity_envelope_switching_failure():
    env = build_validity_envelope(
        projection_available=True,
        switching_safe=False,
        exponential_safe=True,
        kappa_safe=True,
        adaptive_available=True,
        adaptive_band="stable",
    )
    assert env.valid is False
    assert env.reason == "switching_violation"


def test_validity_envelope_kappa_failure():
    env = build_validity_envelope(
        projection_available=True,
        switching_safe=True,
        exponential_safe=True,
        kappa_safe=False,
        adaptive_available=True,
        adaptive_band="hard",
    )
    assert env.valid is False
    assert env.reason == "kappa_violation"
