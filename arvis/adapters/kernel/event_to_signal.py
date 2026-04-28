# arvis/adapters/kernel/event_to_signal.py

from datetime import UTC, datetime
from uuid import uuid4

from arvis.api.signals import Signal, SignalEvent


def event_to_signal(event: SignalEvent) -> Signal:
    return Signal(
        signal_id=f"sig-{uuid4()}",
        timestamp=datetime.now(UTC),
        payload={
            "event_id": event.event_id,
            "type": event.signal_type,
            "payload": event.payload,
        },
        origin=event.source,
    )
