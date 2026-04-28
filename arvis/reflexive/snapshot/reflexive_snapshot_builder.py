# arvis/reflexive/snapshot/reflexive_snapshot_builder.py

from datetime import UTC, datetime
from typing import Any

from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_memory import (
    IRGTimelineTemporalMemory,
)
from arvis.reflexive.timeline.explanation import (
    ReflexiveTimelineExposureExplanation,
)
from arvis.reflexive.timeline.explanation.irg_timeline_explanation_builder import (
    IRGTimelineExplanationBuilder,
)


class ReflexiveSnapshotBuilder:
    """
    Reflexive Snapshot Builder
    """

    @staticmethod
    def build(
        *,
        capabilities: Any,
        timeline_views: dict[str, Any],
        irg_temporal_memory: IRGTimelineTemporalMemory | None = None,
        cognitive_state: Any | None = None,
        introspection: Any | None = None,
        generated_at: datetime | None = None,
    ) -> ReflexiveSnapshot:
        generated_at = generated_at or datetime.now(UTC)

        roles: list[Any] = []
        has_any_public_view = False

        for view in timeline_views.values():
            role = getattr(view, "role", None)

            if role is not None:
                roles.append(role)
                if getattr(role, "is_public", False):
                    has_any_public_view = True

        timeline_explanation = ReflexiveTimelineExposureExplanation.build(
            roles,
            has_any_public_view=has_any_public_view,
        )

        irg_explanation = None
        if irg_temporal_memory is not None:
            irg_explanation = IRGTimelineExplanationBuilder.build(irg_temporal_memory)

        return ReflexiveSnapshot(
            capabilities=capabilities,
            cognitive_state=cognitive_state,
            timeline_views=timeline_views,
            introspection=introspection,
            generated_at=generated_at,
            timeline_explanation=timeline_explanation,
            irg_explanation=irg_explanation,
        )
