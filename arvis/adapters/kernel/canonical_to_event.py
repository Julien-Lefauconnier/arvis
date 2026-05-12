# arvis/adapters/kernel/canonical_to_event.py

from arvis.signals.canonical.canonical_signal import CanonicalSignal
from arvis.signals.signal_event import SignalEvent
from arvis.types.identifiers import deterministic_id
from arvis.types.timestamps import utcnow


def canonical_to_event(canonical: CanonicalSignal) -> SignalEvent:
    return SignalEvent(
        event_id=deterministic_id(
            "evt",
            canonical.signal_id,
            canonical.key.code,
            canonical.temporal_anchor,
        ),
        created_at=utcnow(),
        signal_type=canonical.key.code,
        source=canonical.origin,
        payload={
            "signal_id": canonical.signal_id,
            "state": canonical.state,
            "subject_ref": canonical.subject_ref,
            "temporal_anchor": canonical.temporal_anchor,
        },
    )
