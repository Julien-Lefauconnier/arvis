# tests/api/test_stability_view.py

from arvis.api.stability import StabilityView
from arvis.stability.stability_snapshot import StabilitySnapshot


def test_stability_view_mapping():
    snapshot = StabilitySnapshot(
        verdict="unstable",
        score=0.3,
        confidence=0.8,
        samples=15,
        mean_dv=0.05,
        std_dv=0.07,
        instability_rate=0.4,
        collapse_risk=0.6,
        last_v=0.9,
        reasons=["high drift"],
    )

    view = StabilityView.from_snapshot(snapshot)

    assert view.stability_score == 0.3
    assert view.risk_level == 0.6
    assert view.regime == "unstable"
