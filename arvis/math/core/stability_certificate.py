# arvis/math/core/stability_certificate.py
"""Stability certificate for the v0 contraction monitor's fast loop.

Proven, sequence-agnostic guarantees: they hold for ANY input sequence,
adversarial or not, because they follow from the construction of the energy,
not from observed samples:

  (I) Compact invariant (bounded-input bounded-state). Every turn the
      operational state x = (budget_used, risk, uncertainty, governance) is
      clamped to ``[STATE_LOWER, STATE_UPPER]`` = [0, 1]^4, so the energy
      ``V(x) = sum_i w_i * x_i`` and the hybrid drift both stay in [0, 1]. No
      input can drive the governed state out of this compact set: there is no
      blow-up.

  (II) Bounded adversarial leverage (Lipschitz energy). V is a convex
      combination of clamped signals and ``clamp01`` is non-expansive, hence
          |V(x) - V(x')| <= sum_i w_i * |x_i - x'_i| <= ||x - x'||_inf .
      An adversary moving signal i by eps shifts V by at most ``w_i * eps``;
      moving every signal by eps shifts V by at most eps. The energy cannot be
      amplified: a per-turn jump in V is bounded by the per-turn input move.

These are derived from the weights (see :func:`certify`) and machine-checked by
``tests/math/core/test_contraction_stability.py``, which SEARCHES adversarially
for a violating sequence and finds none.

NOT claimed here: a global Lyapunov contraction proof (the composite-W slow loop
stays out of scope), nor PAC coverage of the risk ceiling under non-i.i.d.
sequences. ``risk_ucb`` adds a Hoeffding term ``sqrt(log(1/delta)/(2n))`` that is
only a true confidence bound when violation events are i.i.d.; under a crafted
(adversarial) sequence it degrades to a sampling margin. Making the certified
risk adversarially valid (a time-uniform confidence sequence) is future work.
"""

from __future__ import annotations

from dataclasses import dataclass

from arvis.math.lyapunov.lyapunov import LyapunovWeights

# The operational state is clamped to this compact box every turn.
STATE_LOWER = 0.0
STATE_UPPER = 1.0


@dataclass(frozen=True)
class StabilityCertificate:
    """Proven fast-loop guarantees, derived from the energy weights.

    axis_leverage:
        Per-axis Lipschitz constants of V (the normalized convex weights). An
        adversary moving axis ``i`` by ``eps`` moves V by at most
        ``axis_leverage[i] * eps``.
    energy_lipschitz_inf:
        Lipschitz constant of V in the sup norm (the sum of the weights = 1 for
        convex weights): moving every axis by ``eps`` moves V by at most this.
    state_lower / state_upper:
        The compact invariant box each axis: and hence V and the drift:
        provably stays inside.
    """

    axis_leverage: tuple[float, float, float, float]
    energy_lipschitz_inf: float
    state_lower: float
    state_upper: float

    def energy_move_bound(self, dx: tuple[float, float, float, float]) -> float:
        """Proven upper bound on ``|V(x') - V(x)|`` for an input move ``dx``.

        Returns ``sum_i axis_leverage[i] * |dx_i|`` where ``dx = x' - x``. By
        construction the true energy change never exceeds this value.
        """
        return float(
            sum(w * abs(d) for w, d in zip(self.axis_leverage, dx, strict=True))
        )


def certify(weights: LyapunovWeights | None = None) -> StabilityCertificate:
    """Derive the fast-loop stability certificate from the energy weights."""
    w = (weights or LyapunovWeights()).normalized()
    leverage: tuple[float, float, float, float] = (
        w.w_budget,
        w.w_risk,
        w.w_uncertainty,
        w.w_governance,
    )
    return StabilityCertificate(
        axis_leverage=leverage,
        energy_lipschitz_inf=float(sum(leverage)),
        state_lower=STATE_LOWER,
        state_upper=STATE_UPPER,
    )
