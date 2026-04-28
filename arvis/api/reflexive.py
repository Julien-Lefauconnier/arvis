# arvis/api/reflexive.py

from typing import Any, Optional, Dict

from arvis.reflexive.snapshot.reflexive_snapshot_service import ReflexiveSnapshotService
from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot


def get_reflexive_snapshot(
    state: Any,
    context: Optional[Dict[str, Any]] = None,
) -> ReflexiveSnapshot:
    """
    Point d’entrée officiel de la réflexivité ARVIS.
    """

    service = ReflexiveSnapshotService()
    context = context or {}

    if not isinstance(context, dict):
        context = {}

    return service.build_snapshot(
        timeline_views=context.get("timeline_views", {}) or {},
        irg_temporal_memory=context.get("irg_temporal_memory"),
        cognitive_state=state,
        introspection=context.get("introspection"),
        generated_at=context.get("generated_at"),
    )
