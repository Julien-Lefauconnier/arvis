# tests/math/core/test_contraction_benchmark.py
"""Offline contraction benchmark for the v0 ContractionMonitorCore.

Validates the certified-monitor claims on controlled synthetic sessions
(no production dependency, deterministic, CI-runnable):

* nominal sessions stay contracting (delta_v <= 0) with zero observed risk;
* risky sessions drive the windowed risk (p_hat) to ~1 and a CRITICAL verdict;
* the two regimes are clearly discriminated by collapse_risk;
* a converging session contracts (energy decreases, delta_v <= 0 dominates);
* a perturbation spikes delta_v > 0 then re-contracts, and the windowed risk
  decays once the violation ages out of the window.
"""

from __future__ import annotations

from typing import Any

from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
    MonitorSnapshot,
)


def _frame(n_axes: int) -> Any:
    return type("UncertaintyFrame", (), {"axes": set(range(n_axes))})()


def _bundle(
    *,
    confidence: float,
    roles: tuple[str, ...] = (),
    n_axes: int = 0,
    reason: str = "informational_query",
    memory_pressure: float = 0.0,
) -> Any:
    retrieval = type(
        "RetrievalSnapshot",
        (),
        {"confidence": confidence, "scores": [], "semantic_roles": list(roles)},
    )()
    decision = type(
        "DecisionResult",
        (),
        {"uncertainty_frames": [_frame(n_axes)] if n_axes else [], "reason": reason},
    )()
    return type(
        "Bundle",
        (),
        {
            "retrieval_snapshot": retrieval,
            "decision_result": decision,
            "memory_features": {"memory_pressure": memory_pressure},
        },
    )()


def _run_session(
    bundles: list[Any], cfg: MonitorConfig | None = None
) -> list[MonitorSnapshot]:
    core = ContractionMonitorCore(cfg)
    snaps: list[MonitorSnapshot] = []
    state: dict[str, Any] | None = None
    for bundle in bundles:
        snap, state = core.compute(bundle, state)
        snaps.append(snap)
    return snaps


def _fraction_stable(snaps: list[MonitorSnapshot]) -> float:
    return sum(1 for s in snaps if s.stable) / len(snaps)


def test_nominal_session_contracts_with_zero_risk() -> None:
    snaps = _run_session(
        [_bundle(confidence=0.95, roles=("author", "date")) for _ in range(30)]
    )
    # p_hat (fast signal) is exactly zero; the session fully contracts.
    assert all(s.collapse_risk == 0.0 for s in snaps)
    assert _fraction_stable(snaps) == 1.0
    assert max(s.delta_v for s in snaps) == 0.0


def test_certified_ceiling_stays_cautious_then_tightens() -> None:
    # The PAC verdict is honest about sampling: the certified ceiling (risk_ucb)
    # starts wide and tightens monotonically as evidence accrues, even while the
    # fast signal (p_hat) is already pinned at zero.
    snaps = _run_session([_bundle(confidence=0.95) for _ in range(200)])
    ucb = [s.risk_ucb for s in snaps]
    assert all(s.collapse_risk == 0.0 for s in snaps)
    assert ucb[-1] < ucb[5]
    assert all(b <= a + 1e-9 for a, b in zip(ucb, ucb[1:], strict=False))


def test_risky_session_saturates_risk_and_flags_critical() -> None:
    snaps = _run_session(
        [
            _bundle(confidence=0.1, roles=("x",), n_axes=2, reason="action_request")
            for _ in range(30)
        ]
    )
    assert snaps[-1].collapse_risk >= 0.9
    assert snaps[-1].risk_verdict == "CRITICAL"


def test_regimes_are_discriminated_by_collapse_risk() -> None:
    nominal = _run_session([_bundle(confidence=0.95) for _ in range(30)])
    risky = _run_session([_bundle(confidence=0.1, n_axes=2) for _ in range(30)])
    assert risky[-1].collapse_risk - nominal[-1].collapse_risk >= 0.9


def test_converging_session_contracts() -> None:
    # confidence climbs 0.1 -> 0.95: measured risk falls, energy decreases.
    n = 20
    bundles = [
        _bundle(confidence=0.1 + (0.85 * i / (n - 1)), n_axes=0) for i in range(n)
    ]
    snaps = _run_session(bundles)
    # energy is non-increasing overall and delta_v <= 0 dominates (contraction)
    assert snaps[-1].energy_v <= snaps[0].energy_v
    assert _fraction_stable(snaps) >= 0.8
    # observed risk does not grow as the session improves
    assert snaps[-1].collapse_risk <= snaps[0].collapse_risk


def test_perturbation_spikes_then_recontracts_and_risk_decays() -> None:
    # small risk window so the violation visibly ages out
    cfg = MonitorConfig(risk_window=4)
    pre = [_bundle(confidence=0.95) for _ in range(8)]
    spike = [_bundle(confidence=0.05, n_axes=3, reason="action_request")]
    post = [_bundle(confidence=0.95) for _ in range(8)]
    snaps = _run_session(pre + spike + post, cfg)

    spike_idx = len(pre)
    # the spike breaks contraction (energy jumps up), the next turn re-contracts
    assert snaps[spike_idx].delta_v > 0.0
    assert snaps[spike_idx].stable is False
    assert snaps[spike_idx + 1].delta_v < 0.0
    assert snaps[spike_idx + 1].stable is True
    # the windowed risk peaks around the spike and decays as it ages out
    assert snaps[spike_idx].collapse_risk > snaps[-1].collapse_risk
    assert snaps[-1].collapse_risk == 0.0


def test_regime_is_classified_after_enough_samples() -> None:
    snaps = _run_session([_bundle(confidence=0.95) for _ in range(30)])
    # once the delta_v history has enough samples, a regime label is emitted
    assert isinstance(snaps[-1].regime, str)
    assert snaps[-1].regime != ""


def test_verdict_earns_trust_with_evidence() -> None:
    # The certified verdict starts CRITICAL (no evidence), passes through WARN,
    # and only reaches OK once a clean full window certifies low risk.
    snaps = _run_session([_bundle(confidence=0.95) for _ in range(200)])
    verdicts = [s.risk_verdict for s in snaps]
    assert verdicts[0] == "CRITICAL"
    assert "WARN" in verdicts
    assert verdicts[-1] == "OK"


def test_risky_session_never_reaches_ok() -> None:
    snaps = _run_session([_bundle(confidence=0.1, n_axes=2) for _ in range(200)])
    assert all(s.risk_verdict != "OK" for s in snaps)
    assert snaps[-1].risk_verdict == "CRITICAL"
