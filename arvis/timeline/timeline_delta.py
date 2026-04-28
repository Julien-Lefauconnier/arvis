# arvis/timeline/timeline_delta.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, List

from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_cursor import TimelineCursor
from arvis.timeline.timeline_snapshot import TimelineSnapshot


# ============================================================
# Errors
# ============================================================


class TimelineDeltaError(ValueError):
    pass


class TimelineDeltaBaseMismatch(TimelineDeltaError):
    pass


class TimelineDeltaTargetMismatch(TimelineDeltaError):
    pass


class TimelineDeltaEmptyError(TimelineDeltaError):
    pass


class TimelineDeltaDecodeError(TimelineDeltaError):
    pass


# ============================================================
# helpers: framing
# ============================================================


def _pack_frames(frames: List[bytes]) -> bytes:
    out = bytearray()
    for f in frames:
        out += len(f).to_bytes(4, "big")
        out += f
    return bytes(out)


def _unpack_frames(blob: bytes) -> List[bytes]:
    out: List[bytes] = []
    i = 0
    n = len(blob)
    while i < n:
        if i + 4 > n:
            raise TimelineDeltaDecodeError("truncated frame length")
        ln = int.from_bytes(blob[i : i + 4], "big")
        i += 4
        if ln == 0:
            raise TimelineDeltaDecodeError("empty frame not allowed")
        if ln < 0 or i + ln > n:
            raise TimelineDeltaDecodeError("invalid frame length")
        out.append(blob[i : i + ln])
        i += ln
    if i != n:
        raise TimelineDeltaDecodeError("extra bytes after frames")
    return out


# ============================================================
# TimelineDelta
# ============================================================


@dataclass(frozen=True)
class TimelineDelta:
    """
    Immutable append-only delta.

    Guarantees:
    - deterministic replay
    - append-only
    - distributed sync safe
    - rollback detection
    """

    base: TimelineCursor
    target: TimelineCursor
    entries: Tuple[TimelineEntry, ...]

    def __post_init__(self) -> None:
        if self.entries is None:
            raise TimelineDeltaError("entries must not be None")
        if len(self.entries) == 0:
            raise TimelineDeltaEmptyError("timeline delta cannot be empty")
        if self.base is None or self.target is None:
            raise TimelineDeltaError("base and target must not be None")
        if self.base.total_entries + len(self.entries) != self.target.total_entries:
            raise TimelineDeltaError("delta length mismatch with target cursor")
        # ensure entries are immutable tuple
        if not isinstance(self.entries, tuple):
            raise TimelineDeltaError("entries must be a tuple")

        for e in self.entries:
            if e is None:
                raise TimelineDeltaError("entry must not be None")

        ids = [e.entry_id for e in self.entries]
        if len(ids) != len(set(ids)):
            raise TimelineDeltaError("duplicate entries in delta")

    # --------------------------------------------------
    # Core apply
    # --------------------------------------------------
    def apply_to(self, snap: TimelineSnapshot) -> TimelineSnapshot:
        if snap is None:
            raise TimelineDeltaError("snapshot must not be None")
        if snap.cursor() != self.base:
            raise TimelineDeltaBaseMismatch("snapshot cursor does not match delta base")

        out = snap
        for e in self.entries:
            if e is None:
                raise TimelineDeltaError("entry must not be None")
            out = out.append(e)

        cursor = out.cursor()
        if cursor != self.target:
            raise TimelineDeltaTargetMismatch(
                "resulting snapshot cursor does not match delta target"
            )
        return out

    # --------------------------------------------------
    # Verification
    # --------------------------------------------------
    def verify_against(self, snap: TimelineSnapshot) -> None:
        if snap is None:
            raise TimelineDeltaError("snapshot must not be None")
        if snap.cursor() != self.base:
            raise TimelineDeltaBaseMismatch(
                "snapshot cursor mismatch during verification"
            )
        # simulate application without allocation explosion
        expected_total = snap.cursor().total_entries + len(self.entries)

        if expected_total != self.target.total_entries:
            raise TimelineDeltaTargetMismatch("delta does not match target cardinality")

    # --------------------------------------------------
    # Builders
    # --------------------------------------------------
    @classmethod
    def from_snapshots(
        cls,
        base: TimelineSnapshot,
        target: TimelineSnapshot,
    ) -> "TimelineDelta":
        """
        Build an append-only delta between two snapshots.

        Guarantees:
        - deterministic
        - append-only
        - rollback detection
        """

        base_cursor = base.cursor()
        target_cursor = target.cursor()

        # --- no rollback ---
        if target_cursor.total_entries < base_cursor.total_entries:
            raise TimelineDeltaError("target snapshot is older than base")

        # --- trivial mismatch ---
        if target_cursor.total_entries == base_cursor.total_entries:
            raise TimelineDeltaEmptyError("no delta between identical snapshots")

        # --- extract appended entries ---
        start = base_cursor.total_entries
        end = target_cursor.total_entries

        # --------------------------------------------------
        # VALIDATE APPEND-ONLY INTEGRITY (CRITICAL)
        # --------------------------------------------------
        base_len = base_cursor.total_entries

        if tuple(target.entries[:base_len]) != tuple(base.entries):
            raise TimelineDeltaError("target is not an append-only extension of base")

        try:
            new_entries = target.entries[start:end]
        except Exception as e:
            raise TimelineDeltaError("cannot extract delta entries") from e

        if len(new_entries) == 0:
            raise TimelineDeltaEmptyError("delta extraction failed")

        # defensive copy + immutability
        new_entries = tuple(new_entries)

        if any(e is None for e in new_entries):
            raise TimelineDeltaError("delta contains invalid entries")

        return cls(
            base=base_cursor,
            target=target_cursor,
            entries=tuple(new_entries),
        )

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def size(self) -> int:
        return len(self.entries)
