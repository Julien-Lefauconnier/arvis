# arvis/adapters/kernel/event_to_signal.py

from arvis.signals.signal import Signal
from arvis.signals.signal_event import SignalEvent
from arvis.types.identifiers import deterministic_id
from arvis.types.timestamps import utcnow


def event_to_signal(event: SignalEvent) -> Signal:
    return Signal(
        signal_id=deterministic_id(
            "sig",
            event.event_id,
            event.signal_type,
        ),
        timestamp=utcnow(),
        payload={
            "event_id": event.event_id,
            "type": event.signal_type,
            "payload": event.payload,
        },
        origin=event.source,
    )
