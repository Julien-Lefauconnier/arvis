# arvis/timeline/timeline_commitment.py

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256

from .timeline_snapshot import TimelineSnapshot


def _sha256_hex(data: bytes) -> str:
    return sha256(data).hexdigest()


def _canonical_bytes(
    head: str | None,
    total_entries: int,
    timestamp_iso: str,
) -> bytes:
    """
    Stable canonical serialization.

    Simpler than TLV while remaining deterministic.
    """
    payload = {
        "head": head,
        "total_entries": total_entries,
        "timestamp": timestamp_iso,
    }

    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )

    return raw.encode("utf-8")


@dataclass(frozen=True)
class TimelineCommitment:
    """
    Deterministic cryptographic commitment to a timeline state.

    Not a signature.
    Can later be signed or attested.
    """

    head: str | None
    total_entries: int
    timestamp_iso: str
    commitment: str

    @classmethod
    def from_snapshot(cls, snap: TimelineSnapshot) -> TimelineCommitment:
        cur = snap.cursor()

        raw = _canonical_bytes(
            cur.head,
            cur.total_entries,
            cur.timestamp.isoformat(),
        )

        return cls(
            head=cur.head,
            total_entries=cur.total_entries,
            timestamp_iso=cur.timestamp.isoformat(),
            commitment=_sha256_hex(raw),
        )

    def verify_against(self, snap: TimelineSnapshot) -> None:
        other = TimelineCommitment.from_snapshot(snap)

        if other != self:
            raise ValueError("TimelineCommitment mismatch")

    def to_bytes(self) -> bytes:
        return _canonical_bytes(
            self.head,
            self.total_entries,
            self.timestamp_iso,
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> TimelineCommitment:
        try:
            obj = json.loads(data.decode("utf-8"))
        except Exception as e:
            raise ValueError("invalid commitment bytes") from e

        head = obj.get("head")
        total_entries = obj["total_entries"]
        timestamp_iso = obj["timestamp"]

        if head is not None:
            if len(head) != 64:
                raise ValueError("invalid head length")
            if any(c not in "0123456789abcdef" for c in head):
                raise ValueError("invalid head format")

        if not isinstance(total_entries, int):
            raise ValueError("invalid total_entries")

        if total_entries < 0:
            raise ValueError("invalid total_entries")

        commitment = _sha256_hex(data)

        return cls(
            head=head,
            total_entries=total_entries,
            timestamp_iso=timestamp_iso,
            commitment=commitment,
        )
