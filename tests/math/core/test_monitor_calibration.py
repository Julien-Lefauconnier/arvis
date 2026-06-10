# tests/math/core/test_monitor_calibration.py
"""Calibration-harness assertions for the v0 ContractionMonitorCore.

Encodes the research-box finding (the default operating point does NOT separate
grounded from weak grounding) and guards that the sweep can FIND an operating
point that does — i.e. that the certified risk is calibratable into a real
"the decision is assured" signal.
"""

from __future__ import annotations

from arvis.math.core.contraction_monitor_core import MonitorConfig
from tests.math.core.monitor_calibration import (
    confidence_mean,
    default_scenarios,
    evaluate,
    recommend,
    replay,
    sweep,
)


def test_replay_is_deterministic() -> None:
    scenario = default_scenarios()[0]
    cfg = MonitorConfig()
    a = [
        s.collapse_risk
        for s in replay(scenario, config=cfg, confidence=confidence_mean)
    ]
    b = [
        s.collapse_risk
        for s in replay(scenario, config=cfg, confidence=confidence_mean)
    ]
    assert a == b


def test_default_operating_point_does_not_separate() -> None:
    # The shipped default (mean confidence, tau_risk=0.5) is exactly the box
    # symptom: grounded risk (~0.35) and weak risk (~0.44) both sit BELOW tau,
    # so collapse_risk stays 0 for both => no separation. This is WHY we sweep.
    res = evaluate(default_scenarios(), transform="mean", tau_risk=0.5)
    assert res.margin == 0.0
    assert res.good_max_phat == 0.0
    assert res.bad_min_phat == 0.0


def test_sweep_finds_a_separating_operating_point() -> None:
    best = recommend(sweep(default_scenarios()), max_false_alarm=0.1)
    assert best is not None
    assert best.separates
    assert best.good_max_phat <= 0.1


def test_recommended_point_keeps_grounded_quiet_and_flags_weak() -> None:
    best = recommend(sweep(default_scenarios()), max_false_alarm=0.1)
    assert best is not None
    per = best.per_scenario
    # GOOD scenarios stay certified-quiet; the weak-grounding one is flagged.
    assert per["grounded_meridien"] == 0.0
    assert per["nominal_greeting"] == 0.0
    assert per["weak_offcorpus"] > 0.0


def test_recommended_point_is_robust_not_razor_thin() -> None:
    # The recommendation must not be a combo that only separates by a hair:
    # tau should sit comfortably above the worst grounded turn's risk.
    best = recommend(sweep(default_scenarios()), max_false_alarm=0.1)
    assert best is not None
    assert best.good_headroom >= 0.1
