# tests/api/test_risk_view_honesty.py
"""The public view reports the certified risk ceiling, not just the rate.

Campaign INTEGRITY (LOT I3 / DM-I3, audit P1-6, 2026-09-02). On a
cold turn the contraction monitor measures an empirical collapse rate
of 0.0 AND a certified PAC ceiling of 1.0 with verdict CRITICAL: the
two mean opposite things (nothing observed yet). The public surface
printed ``Risk=0.00`` and carried neither ``risk_ucb`` nor
``risk_verdict`` anywhere in ``to_dict()``, so a consumer reading the
documented "what the engine's contraction monitor measured" saw calm
where the monitor certified maximal uncertainty.
"""

from __future__ import annotations

from arvis.api.engine import ArvisEngine


def _cold_view():  # type: ignore[no-untyped-def]
    return ArvisEngine().run("u1", {"text": "cold turn probe"})


def test_stability_view_carries_the_certified_ceiling() -> None:
    """RED on the pre-campaign tree: the fields did not exist."""
    view = _cold_view().stability_view

    assert view is not None
    assert view.risk_ucb == 1.0
    assert view.risk_verdict == "CRITICAL"
    assert view.risk_level == 0.0


def test_to_dict_stability_block_exposes_ceiling_and_verdict() -> None:
    payload = _cold_view().to_dict()

    stability = payload["stability"]
    assert stability["risk"] == 0.0
    assert stability["risk_ucb"] == 1.0
    assert stability["risk_verdict"] == "CRITICAL"


def test_summary_prints_the_ceiling_beside_the_rate() -> None:
    """RED on the pre-campaign tree: Risk=0.00 stood alone."""
    line = _cold_view().summary()

    assert "Risk=0.00" in line
    assert "RiskCeiling=1.00 (CRITICAL)" in line


def test_trace_block_separates_regime_from_verdict() -> None:
    """The trace's stability sub-block used to publish a VERDICT under
    the key ``regime``. Both concepts now travel under their own
    names (the trace block is experimental; this is grammar, not
    contract)."""
    from arvis.api.trace import DecisionTraceView

    class _Snapshot:
        score = 0.4
        collapse_risk = 0.1
        regime = "stable"
        verdict = "ALLOW"

    view = DecisionTraceView(
        timestamp="t",
        user_id="u",
        decision=None,
        intent=None,
        gate_verdict=None,
        confirmation_required=False,
        confirmation_granted=None,
        stability=_Snapshot(),
        predictive=None,
        symbolic=None,
        system_tension=0.2,
        has_conflict=False,
        has_governance=False,
        has_pending_actions=False,
    )

    block = view.to_dict()["observability"]["stability"]
    assert block["regime"] == "stable"
    assert block["verdict"] == "ALLOW"
    assert block["risk"] == 0.1
