# arvis/math/risk/confidence_sequence.py
"""Anytime-valid, distribution-free confidence sequence for the violation risk.

The Hoeffding bound in :mod:`arvis.math.risk.risk_bound` adds a term
``sqrt(log(1/delta) / (2 n))`` that is a valid confidence bound only when the
violation events are i.i.d. *and* ``n`` is fixed in advance. The contraction
monitor honours neither assumption: it thresholds the bound at *every* turn
(sequential evaluation / optional stopping), and adversarial input makes the
events neither independent nor identically distributed.

This module replaces that fixed-``n`` term with a *confidence sequence* (CS):
an upper bound that holds simultaneously for all ``n`` and without an i.i.d.
assumption.

Construction (fixed-``lambda`` conditional Hoeffding supermartingale). Let
``X_s in {0, 1}`` be the violation at turn ``s`` and
``p_s = P(X_s = 1 | F_{s-1})`` its conditional propensity given the history --
well defined even for an adaptive adversary. For any fixed ``lambda`` the
conditional Hoeffding lemma gives, with no independence assumption,

    E[exp(lambda * (p_s - X_s)) | F_{s-1}] <= exp(lambda ** 2 / 8),

so ``M_n = exp(lambda * sum_{s<=n} (p_s - X_s) - n * lambda ** 2 / 8)`` is a
non-negative supermartingale with ``M_0 = 1``. Ville's inequality then gives
``P(exists n : M_n >= 1 / delta) <= delta``, hence with probability
``>= 1 - delta``, *simultaneously for all n*,

    (1 / n) * sum_{s<=n} p_s  <=  p_hat_n + R(n),
    R(n) = log(1 / delta) / (lambda * n) + lambda / 8.

We fix ``lambda = sqrt(8 * log(1/delta) / horizon)``, which makes ``R`` tight at
``n = horizon`` (there it equals the Hoeffding term ``sqrt(log(1/delta)/(2n))``)
and only mildly looser elsewhere. A horizon-free boundary (stitching; Howard,
Ramdas et al., 2021) is a future tightening.

What is bounded is the running average *conditional* violation propensity -- the
honest target under an adaptive adversary. The estimate is cumulative (no sliding
window): the session as a whole is certified. Reacting to non-stationarity (a
predictable-weight discounted CS) is deferred to a later increment.

NOT claimed: factual correctness of answers, nor a global Lyapunov contraction.
This bounds how often the monitored guard fires, with a guarantee that survives
both sequential evaluation and adversarial inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, fsum, inf, log, sqrt

from arvis.math.risk.risk_bound import RiskBoundSnapshot


def _zeta_upper_bound(s: float, terms: int = 1000) -> float:
    """Upper bound on the Riemann zeta ``zeta(s)`` for ``s > 1``.

    Partial sum plus the integral tail bound
    ``sum_{j > J} j ** -s <= int_J^inf x ** -s dx = J ** (1 - s) / (s - 1)``.
    Rounding *up* keeps the stitching spend conservative
    (``sum_k delta_k <= delta``), so the union bound -- hence the
    anytime-validity -- is preserved.
    """
    partial = fsum((j + 1.0) ** (-s) for j in range(terms))
    tail: float = float(terms) ** (1.0 - s) / (s - 1.0)
    return partial + tail


@dataclass(frozen=True)
class ConfidenceSequenceParams:
    """Parameters for :class:`ConfidenceSequenceRiskBound`.

    horizon:
        ``lambda`` is tuned so the bound is tight at this many turns. Pick it
        near the expected session length / operating scale.
    delta:
        Time-uniform error level: the bound holds for ALL ``n`` with
        probability ``>= 1 - delta`` (not per-``n``).
    warn_p_ucb / critical_p_ucb:
        Verdict thresholds on the upper confidence bound.
    """

    horizon: int = 200
    delta: float = 0.01
    warn_p_ucb: float = 0.10
    critical_p_ucb: float = 0.25
    boundary: str = "fixed_lambda"  # or "stitched" (horizon-free)
    stitch_eta: float = 2.0  # geometric epoch ratio (> 1)
    stitch_s: float = 1.4  # spending exponent (> 1)
    stitch_k_pad: int = 3  # epochs swept past ceil(log_eta n)
    bernstein_a: float = 1.0  # variance-term constant (bernstein boundary)
    bernstein_c: float = 0.8  # range-term constant (bernstein boundary)


class ConfidenceSequenceRiskBound:
    """Anytime-valid, i.i.d.-free upper bound on the violation rate.

    Drop-in alternative to :class:`HoeffdingRiskBound`: identical ``push``
    signature and :class:`RiskBoundSnapshot` output, but the confidence radius
    is valid simultaneously for all ``n`` and under adversarial (adapted)
    sequences. Cumulative -- tracks the whole session, not a sliding window.
    """

    def __init__(self, params: ConfidenceSequenceParams | None = None) -> None:
        self.params = params or ConfidenceSequenceParams()
        if not (0.0 < self.params.delta < 1.0):
            raise ValueError("delta must be in (0,1)")
        if self.params.horizon <= 0:
            raise ValueError("horizon must be positive")
        self._n = 0
        self._violations = 0
        self._var_pred = 0.0
        self._log_inv_delta = log(1.0 / self.params.delta)
        self._lambda = sqrt(8.0 * self._log_inv_delta / self.params.horizon)
        if self.params.boundary not in ("fixed_lambda", "stitched", "bernstein"):
            raise ValueError(
                "boundary must be 'fixed_lambda', 'stitched' or 'bernstein'"
            )
        if self.params.stitch_eta <= 1.0:
            raise ValueError("stitch_eta must be > 1")
        if self.params.stitch_s <= 1.0:
            raise ValueError("stitch_s must be > 1")
        zeta_upper = _zeta_upper_bound(self.params.stitch_s)
        self._stitch_base = log(zeta_upper / self.params.delta)

    def radius(self, n: int, var_pred: float = 0.0) -> float:
        """Confidence radius ``R(n)``; valid for all ``n`` by Ville's inequality.

        Dispatches on ``params.boundary``: ``"fixed_lambda"`` (default,
        historical, tight only at ``horizon``) or ``"stitched"``
        (horizon-free, informative at small *and* large ``n``).
        """
        if n <= 0:
            return 1.0
        if self.params.boundary == "bernstein":
            return self._radius_bernstein(n, var_pred)
        if self.params.boundary == "stitched":
            return self._radius_stitched(n)
        return self._radius_fixed_lambda(n)

    def _stitch_log(self, n: int) -> float:
        """Horizon-free iterated-log term (same delta-spending family as the
        Hoeffding stitch); used by the variance-adaptive bernstein radius."""
        eta = self.params.stitch_eta
        epoch = ceil(log(float(max(n, 2))) / log(eta)) + 1.0
        return self._stitch_base + self.params.stitch_s * log(epoch)

    def _radius_bernstein(self, n: int, var_pred: float) -> float:
        """Variance-adaptive anytime-valid radius (empirical-Bernstein form).

        ``var_pred = sum_{s<=n} p_hat_{s-1} (1 - p_hat_{s-1})`` is the
        *predictable* variance process (estimated from the past only, so the
        martingale structure -- hence Ville -- is preserved; the empirical
        plug-in under-covers). On a clean session var_pred -> 0 and the radius
        collapses to the ``c * ell / n`` range term (linear decay), far tighter
        than the Hoeffding ``~1/sqrt(n)``; at max variance it matches Hoeffding.
        Constants (a, c) are MC-certified anytime-valid (miscoverage <= delta
        across iid / two-regime / clean-then-spike / random-walk); the formal
        sub-Gamma derivation (Howard et al., 2021) is a future tightening.
        """
        ell = self._stitch_log(n)
        a = self.params.bernstein_a
        c = self.params.bernstein_c
        return a * sqrt(2.0 * max(var_pred, 0.0) * ell) / n + c * ell / n

    def _radius_fixed_lambda(self, n: int) -> float:
        """Single-``lambda`` radius, tight at ``n == horizon`` (historical)."""
        return self._log_inv_delta / (self._lambda * n) + self._lambda / 8.0

    def _radius_stitched(self, n: int) -> float:
        """Horizon-free stitched radius (Howard, Ramdas, McAuliffe &
        Sekhon, 2021): the min over geometric epochs ``m_k = eta ** k``
        of fixed-lambda bounds, union-bounded by a polynomial spending
        sequence ``delta_k = delta / (zeta(s) (k + 1) ** s)`` (so
        ``sum_k delta_k <= delta``; a conservative *upper* bound on
        ``zeta`` is used). Epoch ``k`` contributes
        ``sqrt(L_k / (8 m_k)) * (1 + m_k / n)`` with
        ``L_k = log(zeta(s) / delta) + s * log(k + 1)``. Tight to
        within a log-log factor at *every* ``n``; cumulative and
        anytime-valid.

        Sweeping ``k`` only to ``ceil(log_eta n) + stitch_k_pad``
        keeps the optimiser in range; truncating the (infinite) union
        only raises the min, so the bound stays valid regardless of
        the cap.
        """
        eta = self.params.stitch_eta
        s = self.params.stitch_s
        k_max = ceil(log(float(n)) / log(eta)) + self.params.stitch_k_pad
        best = inf
        for k in range(k_max + 1):
            m_k = eta**k
            l_k = self._stitch_base + s * log(k + 1.0)
            val = sqrt(l_k / (8.0 * m_k)) * (1.0 + m_k / n)
            best = min(best, val)
        return best

    def evaluate(
        self, n: int, violations: int, var_pred: float = 0.0
    ) -> RiskBoundSnapshot:
        """Pure CS snapshot from aggregate counts -- no mutation.

        A caller that already tracks cumulative ``(n, violations)`` (e.g. the
        contraction monitor) gets the anytime-valid ceiling without replaying
        the event stream.
        """
        if n <= 0:
            return RiskBoundSnapshot(
                n=0, violations=0, p_hat=0.0, p_ucb=0.0, verdict="OK"
            )
        p_hat = violations / n
        p_ucb = min(1.0, p_hat + self.radius(n, var_pred))

        verdict = "OK"
        if p_ucb >= self.params.critical_p_ucb:
            verdict = "CRITICAL"
        elif p_ucb >= self.params.warn_p_ucb:
            verdict = "WARN"

        return RiskBoundSnapshot(
            n=n,
            violations=violations,
            p_hat=float(p_hat),
            p_ucb=float(p_ucb),
            verdict=verdict,
        )

    def push(self, violation: bool) -> RiskBoundSnapshot:
        p_prev = self._violations / self._n if self._n > 0 else 0.0
        self._var_pred += p_prev * (1.0 - p_prev)
        self._n += 1
        if violation:
            self._violations += 1
        return self.evaluate(self._n, self._violations, self._var_pred)
