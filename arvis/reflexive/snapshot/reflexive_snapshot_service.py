# arvis/reflexive/services/reflexive_snapshot_service.py

from typing import Dict, Optional, Any
from datetime import datetime, timezone
from dataclasses import replace

from arvis.reflexive.snapshot.reflexive_snapshot_builder import (
    ReflexiveSnapshotBuilder,
)
from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_memory import (
    IRGTimelineTemporalMemory,
)
from arvis.reflexive.capabilities.capability_snapshot_builder import (
    build_capability_snapshot,
)
from arvis.reflexive.introspection.arvis_introspection_service import (
    ArvisIntrospectionService
)
from arvis.reflexive.attestation.reflexive_attestation import ReflexiveAttestation


class ReflexiveSnapshotService:
    """
    Reflexive Snapshot Service
    """

    def build_snapshot(
        self,
        *,
        timeline_views: Dict[str, object],
        irg_temporal_memory: Optional[IRGTimelineTemporalMemory] = None,
        cognitive_state: Optional[object] = None,
        introspection: Optional[Dict[str, Any]] = None,
        generated_at: Optional[datetime] = None,
    ) -> ReflexiveSnapshot:
        """
        Build a reflexive snapshot for the current system state.
        """

        if introspection is None:
            introspection = ArvisIntrospectionService().build_system_overview()

        if generated_at is None:
            generated_at = datetime.now(timezone.utc)

        snapshot = ReflexiveSnapshotBuilder.build(
            capabilities=build_capability_snapshot(),
            timeline_views=timeline_views,
            irg_temporal_memory=irg_temporal_memory,
            cognitive_state=cognitive_state,
            introspection=introspection,
            generated_at=generated_at,
        )

        rendered: Dict[str, Any] = snapshot.to_dict()
        rendered["exposed_views"] = list(rendered.get("timeline_views", {}).keys())

        attestation = ReflexiveAttestation.from_rendered_payload(rendered)

        return replace(snapshot, attestation=attestation)