# arvis/adapters/kernel/event_to_signal.py

from datetime import datetime, timezone
from uuid import uuid4
from arvis.api.signals import Signal, SignalEvent


def event_to_signal(event: SignalEvent) -> Signal:
    return Signal(
        signal_id=f"sig-{uuid4()}",
        timestamp=datetime.now(timezone.utc),
        payload={
            "event_id": event.event_id,
            "type": event.signal_type,
            "payload": event.payload,
        },
        origin=event.source,
    )
