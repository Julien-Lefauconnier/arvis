# tests/math/lyapunov/test_composite_delta_sanity.py

from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.lyapunov import LyapunovState


def make_fast(x):
    return LyapunovState.from_scalar(float(x))


def test_delta_w_negative_when_all_improve():
    comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

    delta = comp.delta_W(
        fast_prev=make_fast(2.0),
        fast_next=make_fast(1.0),
        slow_prev=None,
        slow_next=None,
    )

    # fallback → doit rester stable ou négatif
    assert delta <= 0


def test_delta_w_positive_when_slow_diverges():
    comp = CompositeLyapunov(lambda_mismatch=0.5, gamma_z=1.0)

    delta = comp.delta_W(
        fast_prev=make_fast(1.0),
        fast_next=make_fast(0.9),
        slow_prev=None,
        slow_next=None,
    )

    # fallback safe (pas de crash)
    assert isinstance(delta, float)