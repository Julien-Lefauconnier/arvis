# arvis/reflexive/snapshot/reflexive_snapshot_builder.py

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from arvis.reflexive.snapshot.reflexive_snapshot import (
    ReflexiveSnapshot,
)
from arvis.reflexive.timeline.explanation.reflexive_timeline_exposure_explanation import (
    ReflexiveTimelineExposureExplanation,
)
from arvis.reflexive.timeline.explanation.irg_timeline_explanation_builder import (
    IRGTimelineExplanationBuilder,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_memory import (
    IRGTimelineTemporalMemory,
)


class ReflexiveSnapshotBuilder:
    """
    Reflexive Snapshot Builder

    Deterministic, declarative assembler for ReflexiveSnapshot.

    This builder:
    - contains no business logic
    - performs no inference
    - exposes no cognitive internals
    - is future-proof for governance & access layers
    """

    @staticmethod
    def build(
        *,
        capabilities: Any,
        timeline_views: Dict[str, Any],
        irg_temporal_memory: Optional[IRGTimelineTemporalMemory] = None,
        cognitive_state: Optional[Any] = None,
        introspection: Optional[Any] = None,
        generated_at: Optional[datetime] = None,
    ) -> ReflexiveSnapshot:
        """
        Assemble a ReflexiveSnapshot from declarative components.
        """

        generated_at = generated_at or datetime.now(timezone.utc)

        # --------------------------------------------------
        # Timeline exposure explanation (surface-level)
        # --------------------------------------------------
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

        # --------------------------------------------------
        # IRG timeline evolution explanation (deep, passive)
        # --------------------------------------------------
        irg_explanation = None
        if irg_temporal_memory is not None:
            irg_explanation = IRGTimelineExplanationBuilder.build(irg_temporal_memory)

        # --------------------------------------------------
        # Assemble snapshot
        # --------------------------------------------------
        return ReflexiveSnapshot(
            capabilities=capabilities,
            cognitive_state=cognitive_state,
            timeline_views=timeline_views,
            introspection=introspection,
            generated_at=generated_at,
            timeline_explanation=timeline_explanation,
            irg_explanation=irg_explanation,
        )
