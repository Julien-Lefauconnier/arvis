# arvis/adapters/kernel/timeline_from_signals.py

from __future__ import annotations

from datetime import datetime, timezone

from veramem_kernel.signals.signal_journal import SignalJournal
from veramem_kernel.api.timeline import TimelineEntry, TimelineSnapshot
from veramem_kernel.journals.timeline.timeline_entry import TimelineEntryNature
from veramem_kernel.journals.timeline.timeline_types import TimelineEntryType


def signal_journal_to_timeline_snapshot(journal: SignalJournal) -> TimelineSnapshot:
    signals = journal.list_signals()
    entries = tuple(_signal_to_timeline_entry(signal, lamport=i) for i, signal in enumerate(signals))
    return TimelineSnapshot.build(entries)


def _signal_to_timeline_entry(signal: object, *, lamport: int) -> TimelineEntry:
    signal_id = getattr(signal, "signal_id", f"timeline-entry-{lamport}")
    timestamp = getattr(signal, "timestamp", None)
    if not isinstance(timestamp, datetime):
        # fallback = stable, not "now"
        timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

    origin = getattr(signal, "origin", None) or "signal"

    key = getattr(signal, "key", None)
    signal_code = getattr(key, "code", "system_notice")

    description = _build_description(signal)

    return TimelineEntry(
        entry_id=signal_id,
        created_at=timestamp,
        type=_map_signal_type(signal_code),
        title=_build_title(signal_code),
        description=description,
        action_id=None,
        place_id=None,
        origin_ref=origin,
        nature=TimelineEntryNature.EVENT,
        device_id="0" * 64,
        lamport=lamport,
    )


def _map_signal_type(signal_code: str) -> TimelineEntryType:
    normalized = signal_code.strip().lower()

    mapping = {
        "decision_emitted": TimelineEntryType.SYSTEM_NOTICE,
        "conflict_detected": TimelineEntryType.SYSTEM_NOTICE,
        "uncertainty_detected": TimelineEntryType.SYSTEM_NOTICE,
        "instability_detected": TimelineEntryType.SYSTEM_NOTICE,
        "early_warning_detected": TimelineEntryType.SYSTEM_NOTICE,
        "ghost_signal": TimelineEntryType.SYSTEM_NOTICE,
        "memory_long_projected": TimelineEntryType.SYSTEM_NOTICE,
    }

    return mapping.get(normalized, TimelineEntryType.SYSTEM_NOTICE)


def _build_title(signal_type: str) -> str:
    return signal_type.replace("_", " ").strip().capitalize()


def _build_description(signal: object) -> str | None:
    parts: list[str] = []

    subject_ref = getattr(signal, "subject_ref", None)
    temporal_anchor = getattr(signal, "temporal_anchor", None)
    state = getattr(signal, "state", None)

    if subject_ref:
        parts.append(f"subject_ref={subject_ref}")
    if temporal_anchor:
        parts.append(f"temporal_anchor={temporal_anchor}")
    if state:
        parts.append(f"state={state}")

    return ", ".join(parts) if parts else None