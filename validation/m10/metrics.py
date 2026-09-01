# validation/m10/metrics.py
"""The nine metric families of M10 section 5, computed from a run.

Pure functions from a list of TurnMeasurement to observed values; the
pass/fail judgment against the pre-registered thresholds lives in
``thresholds.py`` so the observation and the criterion stay separate
(the protocol's pre-registration discipline).
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from validation.m10.runner import TurnMeasurement

_EPS = 1e-12


def _finite(values: list[float | None]) -> list[float]:
    return [float(v) for v in values if v is not None and math.isfinite(float(v))]


def _share(count: int, total: int) -> float:
    return count / total if total else 0.0


def lyapunov_evolution(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.1: distribution of the energy deltas the gate consumed."""
    deltas = _finite([m.delta_w for m in ms if m.turn_index > 0])
    contraction = sum(1 for d in deltas if d < -_EPS)
    marginal = sum(1 for d in deltas if abs(d) <= _EPS)
    expansion = sum(1 for d in deltas if d > _EPS)
    total = len(deltas)
    return {
        "samples": total,
        "p_contraction": _share(contraction, total),
        "p_marginal": _share(marginal, total),
        "p_expansion": _share(expansion, total),
        "max_expansion": max(deltas, default=0.0),
        "mean_delta": sum(deltas) / total if total else 0.0,
    }


def iss_residual(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.2: boundedness of the energy under the corpus perturbations,
    per trajectory: sup W over the trajectory and the empirical gain
    against the largest injected perturbation component."""
    by_trajectory: dict[str, list[TurnMeasurement]] = {}
    for m in ms:
        by_trajectory.setdefault(m.trajectory_id, []).append(m)
    sup_w: list[float] = []
    gains: list[float] = []
    for turns in by_trajectory.values():
        ws = _finite([t.w_current for t in turns])
        if not ws:
            continue
        sup_w.append(max(ws))
        perturbations = [max(t.iss_perturbation.values(), default=0.0) for t in turns]
        w_bar = max(perturbations, default=0.0)
        if w_bar > _EPS:
            gains.append(max(ws) / w_bar)
    return {
        "trajectories": len(sup_w),
        "sup_w_max": max(sup_w, default=0.0),
        "sup_w_mean": sum(sup_w) / len(sup_w) if sup_w else 0.0,
        "divergent_trajectories": sum(1 for w in sup_w if not math.isfinite(w)),
        "empirical_gain_max": max(gains, default=None) if gains else None,
    }


def adaptive_estimation(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.3: availability and distribution of the adaptive estimate."""
    available = [m for m in ms if m.adaptive_available]
    margins = _finite([m.kappa_margin for m in ms])
    bands = Counter(m.kappa_band for m in ms if m.kappa_band)
    return {
        "turns": len(ms),
        "available_turns": len(available),
        "availability": _share(len(available), len(ms)),
        "margin_samples": len(margins),
        "margin_mean": sum(margins) / len(margins) if margins else None,
        "band_counts": dict(bands),
    }


def kappa_violations(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.4: violation frequency and the M6 hard invariant (an ABSTAIN
    never relaxes downstream of the gate)."""
    margins = [(m, m.kappa_margin) for m in ms if m.kappa_margin is not None]
    violations = [m for m, margin in margins if margin > 0.0]
    abstain_relaxed = 0
    for m in ms:
        for t in m.verdict_transitions:
            if t.get("before") == "ABSTAIN" and t.get("after") not in (
                "ABSTAIN",
                "REQUIRE_CONFIRMATION",
            ):
                abstain_relaxed += 1
    return {
        "margin_samples": len(margins),
        "violations": len(violations),
        "violation_rate": _share(len(violations), len(margins)),
        "abstain_relaxed_past_confirmation": abstain_relaxed,
    }


_VERDICTS = ("ALLOW", "REQUIRE_CONFIRMATION", "ABSTAIN")


def gate_distribution(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.5: verdict marginals, per family and conditioned on the sign
    of the consumed energy delta.

    Instrument correction (disclosed, campaign MATH-B run 1): the
    first encoder emitted only the verdicts present in the sample, so
    a zero share came back as a MISSING key and the fail-closed judge
    scored the two zero-observation criteria (adversarial ALLOW,
    expansion ALLOW) as unresolvable failures. Every canonical verdict
    now always carries an explicit share; the registered thresholds
    were not touched.
    """

    def dist(sub: list[TurnMeasurement]) -> dict[str, float]:
        counts = Counter(m.final_verdict or "UNKNOWN" for m in sub)
        total = len(sub)
        shares = {k: _share(v, total) for k, v in sorted(counts.items())}
        for verdict in _VERDICTS:
            shares.setdefault(verdict, 0.0)
        return shares

    by_family: dict[str, dict[str, float]] = {}
    for family in sorted({m.family for m in ms}):
        by_family[family] = dist([m for m in ms if m.family == family])
    contraction = [m for m in ms if m.delta_w is not None and m.delta_w < -_EPS]
    expansion = [m for m in ms if m.delta_w is not None and m.delta_w > _EPS]
    return {
        "overall": dist(ms),
        "by_family": by_family,
        "given_contraction": dist(contraction),
        "given_expansion": dist(expansion),
    }


def projection_overrides(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.6: how often the projection-control layer and the enforcement
    stack tightened the assessment verdict."""
    _ORDER = {"ALLOW": 0, "REQUIRE_CONFIRMATION": 1, "ABSTAIN": 2}
    tightened = 0
    comparable = 0
    pi_blocking = 0
    for m in ms:
        if m.pre_verdict in _ORDER and m.final_verdict in _ORDER:
            comparable += 1
            if _ORDER[m.final_verdict] > _ORDER[m.pre_verdict]:
                tightened += 1
        if (m.pi_gate_verdict or "").lower() not in ("", "allow"):
            pi_blocking += 1
    stages = Counter(t.get("stage", "?") for m in ms for t in m.verdict_transitions)
    return {
        "comparable_turns": comparable,
        "final_stricter_than_pre": tightened,
        "tightening_rate": _share(tightened, comparable),
        "pi_gate_non_allow": pi_blocking,
        "transition_stages": dict(stages.most_common()),
    }


def closed_loop_feedback(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.7: the negative feedback invariant, as exported per turn."""
    increases = [m for m in ms if m.closed_loop.get("energy_increase")]
    consistent = [m for m in increases if m.closed_loop.get("control_should_reduce")]
    return {
        "energy_increase_turns": len(increases),
        "control_reduction_signaled": len(consistent),
        "feedback_consistency": _share(len(consistent), len(increases)),
    }


def perturbation_decomposition(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.8: magnitude of each exported perturbation component."""
    components: dict[str, list[float]] = {}
    for m in ms:
        for key, value in m.iss_perturbation.items():
            components.setdefault(key, []).append(value)
    return {
        key: {
            "max": max(values, default=0.0),
            "mean": sum(values) / len(values) if values else 0.0,
        }
        for key, values in sorted(components.items())
    }


def envelope_compliance(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """5.9: envelope validity, overall and restricted to turns whose
    observation stayed inside the projected domain."""
    total = len(ms)
    valid = sum(1 for m in ms if m.envelope_valid)
    in_domain = [m for m in ms if m.projection_domain_valid]
    valid_in_domain = sum(1 for m in in_domain if m.envelope_valid)
    return {
        "turns": total,
        "envelope_valid_rate": _share(valid, total),
        "in_domain_turns": len(in_domain),
        "envelope_valid_rate_in_domain": _share(valid_in_domain, len(in_domain)),
        "domain_valid_rate": _share(len(in_domain), total),
    }


def compute_all(ms: list[TurnMeasurement]) -> dict[str, Any]:
    return {
        "lyapunov_evolution": lyapunov_evolution(ms),
        "iss_residual": iss_residual(ms),
        "adaptive_estimation": adaptive_estimation(ms),
        "kappa_violations": kappa_violations(ms),
        "gate_distribution": gate_distribution(ms),
        "projection_overrides": projection_overrides(ms),
        "closed_loop_feedback": closed_loop_feedback(ms),
        "perturbation_decomposition": perturbation_decomposition(ms),
        "envelope_compliance": envelope_compliance(ms),
    }
