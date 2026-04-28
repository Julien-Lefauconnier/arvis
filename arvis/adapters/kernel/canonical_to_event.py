# arvis/adapters/kernel/canonical_to_event.py

from datetime import UTC, datetime
from uuid import uuid4

from arvis.api.signals import CanonicalSignal, SignalEvent


def canonical_to_event(canonical: CanonicalSignal) -> SignalEvent:
    return SignalEvent(
        event_id=f"evt-{uuid4()}",
        created_at=datetime.now(UTC),
        signal_type=canonical.key.code,
        source=canonical.origin,
        payload={
            "signal_id": canonical.signal_id,
            "state": canonical.state,
            "subject_ref": canonical.subject_ref,
            "temporal_anchor": canonical.temporal_anchor,
        },
    )
