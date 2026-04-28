# kernel/journals/observation_long/observation_long_builder.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from arvis.kernel_core.memory.observation_long_event import (
    ObservationLongEvent,
)
from arvis.kernel_core.memory.observation_long_invariants import (
    validate_observation_long_event,
)


@dataclass
class ObservationLongBuilder:
    """
    Declarative builder for ObservationLongEvent.

    Contract:
    - payload must be JSON-safe
    - zero inference
    - append-only kernel truth
    """

    user_id: str
    source_type: str
    payload: Mapping[str, Any]

    def build(self) -> ObservationLongEvent:
        event = ObservationLongEvent(
            user_id=self.user_id,
            source_type=self.source_type,
            payload=dict(self.payload),
            observed_at=datetime.now(UTC),
        )

        validate_observation_long_event(event)
        return event
