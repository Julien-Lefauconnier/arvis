# arvis/reflexive/irg_timeline_mapper.py

from typing import Any

from arvis.reflexive.timeline.irg_timeline_view import IRGTimelineView


class IRGTimelineMapper:
    """
    Projection IRG-safe d'un TimelineSummary.
    Aucun contenu, aucun raisonnement, aucune entrée.
    """

    @staticmethod
    def from_summary(summary: Any) -> IRGTimelineView:
        return IRGTimelineView(
            total_events=getattr(summary, "total", 0),
            first_timestamp=getattr(summary, "first_timestamp", None),
            last_timestamp=getattr(summary, "last_timestamp", None),
            has_conflicts=bool(getattr(summary, "has_conflicts", False)),
            has_uncertainty=bool(getattr(summary, "has_uncertainty", False)),
            has_gaps=bool(getattr(summary, "has_gaps", False)),
            has_linguistic_constraints=bool(
                getattr(summary, "has_linguistic_constraints", False)
            ),
        )
