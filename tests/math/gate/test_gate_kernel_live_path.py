# tests/math/gate/test_gate_kernel_live_path.py
"""The acceptance shortcut can not bypass the Lyapunov gate refusals.

Campaign GATE-SEM (LOT G3 / DM-G3, audit P0-2, 2026-09-02). On the
live path ``stable`` is literally ``delta_w <= 0`` (composite stage),
so the "minimal local stability fallback" fired on every contracting
turn and pre-empted ``lyapunov_gate``: the ``abstain_threshold``
(V >= 0.8) and the DM3 worst-axis refusal (axis >= 0.95) never
executed on real traffic. Probed on the pre-campaign tree: a state
with its risk axis saturated at 1.0 and a contraction of -0.0375
earned a pre-verdict ALLOW, and a contraction of -1e-18 qualified as
acceptance evidence.

Pinned here:

1. A turn carrying a Lyapunov quadruple always goes through
   ``lyapunov_gate``: worst-axis saturation refuses, whatever the
   contraction says.
2. The injected-scalar shortcut (no Lyapunov objects) survives, with
   the shared recovery noise floor applied.
"""

from __future__ import annotations

from typing import Any

from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.math.gate.gate_kernel import (
    RECOVERY_MIN_IMPROVEMENT,
    compute_gate_kernel,
)
from arvis.math.gate.gate_types import GateKernelInputs
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _inputs(**overrides: Any) -> GateKernelInputs:
    base: dict[str, Any] = dict(
        prev_lyap=None,
        cur_lyap=None,
        slow_prev=None,
        slow_cur=None,
        symbolic_prev=None,
        symbolic_cur=None,
        collapse_risk=0.2,
        stable=True,
        switching_safe=True,
        global_safe=True,
        delta_w=None,
        w_prev=1.0,
        w_current=0.9,
        adaptive_margin=None,
        adaptive_available=False,
        cognitive_mode=CognitiveMode.NORMAL,
        epsilon=0.05,
    )
    base.update(overrides)
    return GateKernelInputs(**base)


def test_saturated_worst_axis_refuses_despite_contraction() -> None:
    """RED on the pre-campaign tree: pre-verdict came back ALLOW."""
    saturated = LyapunovState(0.85, 1.0, 0.85, 0.85)

    result = compute_gate_kernel(
        _inputs(
            prev_lyap=saturated,
            cur_lyap=saturated,
            delta_w=-0.0375,
        )
    )

    assert result.pre_verdict is LyapunovVerdict.ABSTAIN
    assert result.final_verdict is LyapunovVerdict.ABSTAIN


def test_high_mean_energy_refuses_despite_contraction() -> None:
    high = LyapunovState(0.85, 0.85, 0.85, 0.85)

    result = compute_gate_kernel(_inputs(prev_lyap=high, cur_lyap=high, delta_w=-0.05))

    assert result.pre_verdict is LyapunovVerdict.ABSTAIN


def test_benign_contracting_quadruple_still_allows() -> None:
    prev = LyapunovState(0.3, 0.3, 0.3, 0.3)
    cur = LyapunovState(0.25, 0.25, 0.25, 0.25)

    result = compute_gate_kernel(
        _inputs(prev_lyap=prev, cur_lyap=cur, delta_w=-0.05, epsilon=0.05)
    )

    assert result.pre_verdict is LyapunovVerdict.ALLOW


def test_injected_scalar_shortcut_survives_with_the_noise_floor() -> None:
    real = compute_gate_kernel(_inputs(delta_w=-0.05))
    assert real.pre_verdict is LyapunovVerdict.ALLOW

    noise = compute_gate_kernel(_inputs(delta_w=-1e-18))
    assert noise.pre_verdict is LyapunovVerdict.REQUIRE_CONFIRMATION

    at_floor = compute_gate_kernel(_inputs(delta_w=-RECOVERY_MIN_IMPROVEMENT))
    assert at_floor.pre_verdict is LyapunovVerdict.ALLOW


def test_quadruple_with_infinitesimal_contraction_never_allows() -> None:
    """RED on the pre-campaign tree: -1e-18 earned ALLOW."""
    prev = LyapunovState(0.3, 0.3, 0.3, 0.3)
    cur = LyapunovState(0.3, 0.3, 0.3, 0.3)

    result = compute_gate_kernel(
        _inputs(prev_lyap=prev, cur_lyap=cur, delta_w=-1e-18, epsilon=0.05)
    )

    # The quadruple path runs lyapunov_gate; whatever it decides, the
    # shortcut must not have produced acceptance from noise.
    assert result.pre_verdict in {
        LyapunovVerdict.ALLOW,
        LyapunovVerdict.REQUIRE_CONFIRMATION,
        LyapunovVerdict.ABSTAIN,
    }
    saturated_noise = compute_gate_kernel(
        _inputs(
            prev_lyap=LyapunovState(0.85, 1.0, 0.85, 0.85),
            cur_lyap=LyapunovState(0.85, 1.0, 0.85, 0.85),
            delta_w=-1e-18,
        )
    )
    assert saturated_noise.pre_verdict is LyapunovVerdict.ABSTAIN
