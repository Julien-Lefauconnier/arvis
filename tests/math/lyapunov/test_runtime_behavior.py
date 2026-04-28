# tests/math/lyapunov/test_runtime_behavior.py

from arvis.math.lyapunov.composite_lyapunov import CompositeLyapunov
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.switching.switching_runtime import SwitchingRuntime


# COMPOSITE
def test_delta_w_sign_consistency():
    comp = CompositeLyapunov()

    fast_prev = LyapunovState(0.8, 0.8, 0.8, 0.8)
    fast_next = LyapunovState(0.4, 0.4, 0.4, 0.4)

    delta = comp.delta_W(
        fast_prev=fast_prev,
        fast_next=fast_next,
        slow_prev=None,
        slow_next=None,
    )

    assert delta < 0  # amélioration → ΔW négatif


# RUNTIME
def test_switching_runtime_counts_switches():
    rt = SwitchingRuntime()

    rt.update("A")
    rt.update("A")
    rt.update("B")
    rt.update("B")

    assert rt.total_switches == 1
    assert rt.steps_since_switch >= 1
