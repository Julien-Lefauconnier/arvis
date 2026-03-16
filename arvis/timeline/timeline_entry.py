# arvis/timeline/timeline_entry.py

from dataclasses import dataclass
import unicodedata
from datetime import datetime,timezone
from typing import Dict
from typing import Optional
from enum import Enum

from .timeline_types import TimelineEntryType


class TimelineEntryNature(str, Enum):
    """
    Nature of a timeline entry.

    EVENT:
        A punctual, observable occurrence.
    STATE:
        A declarative snapshot of a system or cognitive state.
    """

    EVENT = "event"
    STATE = "state"


@dataclass(frozen=True)
class TimelineEntry:
    entry_id: str
    created_at: datetime
    type: TimelineEntryType
    title: str
    description: Optional[str]
    action_id: Optional[str]
    place_id: Optional[str]
    # 🧭 Declarative traceability reference
    origin_ref: Optional[str] = None
    # 🧩 Entry nature (EVENT / STATE)
    nature: TimelineEntryNature = TimelineEntryNature.EVENT
    device_id: str = "0" * 64
    lamport: int = 0

    def __post_init__(self):
        """
        Enforce Timeline invariants.

        - created_at must always be defined
        - timeline entries are immutable and declarative
        """

        normalized = unicodedata.normalize("NFKC", self.entry_id)
        if normalized != self.entry_id:
            raise ValueError("TimelineEntry.entry_id must be normalized.")

        if not self.entry_id.isascii():
            raise ValueError("TimelineEntry.entry_id must be ASCII.")
        
        if self.created_at is None:
            raise ValueError(
                "TimelineEntry.created_at must not be None "
                "(timeline entries are strictly time-bound)."
            )
        # 🔒 Enforce timezone-aware UTC timestamps
        if self.created_at.tzinfo is None:
            raise ValueError(
                "TimelineEntry.created_at must be timezone-aware (UTC required)"
            )

        if self.created_at.tzinfo != timezone.utc:
            raise ValueError(
                "TimelineEntry.created_at must be in UTC"
            )
        
        if len(self.entry_id) > 256:
            raise ValueError("TimelineEntry.entry_id too long")
        
        if len(self.entry_id) < 8:
            raise ValueError("TimelineEntry.entry_id too short")

        if any(ord(c) < 32 for c in self.entry_id):
            raise ValueError("TimelineEntry.entry_id contains control characters")
        
        # --------------------------
        # Device identity (industry standard: SHA256 fingerprint)
        # --------------------------
        if not isinstance(self.device_id, str):
            raise ValueError("device_id must be str")

        if len(self.device_id) != 64:
            raise ValueError("device_id must be sha256 hex")

        if any(c not in "0123456789abcdef" for c in self.device_id):
            raise ValueError("device_id must be lowercase hex")

        # --------------------------
        # Lamport clock
        # --------------------------
        if not isinstance(self.lamport, int):
            raise ValueError("lamport must be int")

        if self.lamport < 0:
            raise ValueError("lamport must be >= 0")
        
        if self.lamport > 2**63:
            raise ValueError("lamport overflow risk")



    @property
    def timestamp(self) -> datetime:
        """
        Canonical timeline timestamp.

        Alias for created_at to provide a stable,
        semantic API for consumers (tests, API, debug).
        """
        return self.created_at

    # ------------------------------------------------------------------
    # ⚠️ Unsafe constructor (tests / legacy only)
    # ------------------------------------------------------------------
    @classmethod
    def unsafe(
        cls,
        *,
        entry_id: str,
        type: TimelineEntryType,
        title: str,
        description: Optional[str],
        action_id: Optional[str],
        place_id: Optional[str] = None,
        origin_ref: Optional[str] = None,
        nature: TimelineEntryNature = TimelineEntryNature.EVENT,
        created_at: Optional[datetime] = None,
        device_id: str = "0" * 64,
        lamport: int = 0,

    ) -> "TimelineEntry":
        """
        Unsafe constructor for tests and legacy code.

        This bypasses strict temporal invariants and MUST NOT
        be used in production code.
        """
        return cls(
            entry_id=entry_id,
            created_at=created_at or datetime.now(timezone.utc),
            type=type,
            title=title,
            description=description,
            action_id=action_id,
            place_id=place_id,
            origin_ref=origin_ref,
            nature=nature,
            device_id=device_id,
            lamport=lamport,
        )

    @property
    def label(self) -> str:
        """
        Human-readable label for timeline entries.

        Canonical semantic alias used by tests, debug views
        and governance projections.
        """
        if self.description:
            return self.description
        return self.title
    