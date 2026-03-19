# tests/stability/test_stability_projection_api.py

from arvis.stability.stability_state_projector import StabilityStateProjector
from arvis.stability.stability_statistics import StabilityStatistics
from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.api.stability import StabilityView


def test_stability_projection_and_stats():

    projector = StabilityStateProjector()
    stats = StabilityStatistics()

    snapshot = StabilitySnapshot(
        verdict="stable",
        score=0.5,
        confidence=0.9,
        samples=10,
        mean_dv=-0.01,
        std_dv=0.02,
        instability_rate=0.1,
        collapse_risk=0.2,
        last_v=0.4,
        reasons=["stable dynamics"],
    )

    projected = projector.project(snapshot)
    result = stats.compute(projected)
    view = StabilityView.from_snapshot(snapshot)

    assert projected is not None
    assert result is not None
    assert view.stability_score == 0.5
    assert view.risk_level == 0.2
    assert view.regime == "stable"