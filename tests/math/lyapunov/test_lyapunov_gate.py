# tests/math/lyapunov/test_lyapunov_gate.py

from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov_gate import (
    lyapunov_gate,
    LyapunovGateParams,
    LyapunovVerdict,
)


def make_state(v):
    return LyapunovState(
        budget_used=v,
        risk=v,
        uncertainty=v,
        governance=v,
    )


def test_gate_allows_small_change():

    prev = make_state(0.1)
    cur = make_state(0.11)

    verdict = lyapunov_gate(prev, cur, LyapunovGateParams())

    assert verdict in (
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
    )


def test_gate_abstain_when_high_V():

    prev = make_state(0.9)
    cur = make_state(0.9)

    params = LyapunovGateParams(abstain_threshold=0.8)

    verdict = lyapunov_gate(prev, cur, params)

    assert verdict == LyapunovVerdict.ABSTAIN