# arvis/kernel_core/memory/observation_long_writer.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel_core.memory.observation_long_event import (
    ObservationLongEvent,
)
from arvis.kernel_core.memory.observation_long_journal import (
    ObservationLongJournal,
)
from arvis.kernel_core.memory.observation_long_invariants import (
    validate_observation_long_event,
)


@dataclass
class ObservationLongWriter:
    """
    Kernel writer for longitudinal observations.

    Contract:
    - validates invariants
    - append-only
    - no inference
    """

    journal: ObservationLongJournal

    def append(self, event: ObservationLongEvent) -> None:
        validate_observation_long_event(event)
        self.journal.append(event)
