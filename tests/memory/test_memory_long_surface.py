# tests/memory/test_memory_long_surface.py
"""Long-memory surface: snapshots, batch mode, registry and projector.

Campaign RELEASE (LOT R2). Behavior pins on the experimental
long-memory slice: the service builds deterministic snapshots (single
and batch) from whatever the repository returns; the registry's
plain-value whitelist is deny-by-default; the projector emits only
declarative presence signals and ``no_``-prefixed constraint flags,
never payloads (ZKCS).
"""

from __future__ import annotations

from arvis.memory.memory_long_entry import MemoryLongEntry, MemoryLongType
from arvis.memory.memory_long_projector import MemoryLongContextProjector
from arvis.memory.memory_long_registry import MemoryLongRegistry
from arvis.memory.memory_long_service import MemoryLongService
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot
from arvis.types.timestamps import utcnow


def _entry(key: str) -> MemoryLongEntry:
    return MemoryLongEntry(
        memory_type=MemoryLongType.PREFERENCE,
        key=key,
        created_at=utcnow(),
        source="explicit_user",
    )


class _Repo:
    def __init__(self, per_user: dict[str, list[MemoryLongEntry]]) -> None:
        self._per_user = per_user

    def list_entries(self, *, user_id: str):
        return self._per_user.get(user_id, [])

    def list_active_entries(self, *, user_id: str):
        return self._per_user.get(user_id, [])

    def list_active_entries_batch(self, *, user_ids):
        return {u: self._per_user.get(u, []) for u in user_ids}

    def revoke(self, *args, **kwargs):
        raise NotImplementedError


def test_single_user_snapshot_counts_active_entries() -> None:
    service = MemoryLongService(_Repo({"u1": [_entry("language"), _entry("tone")]}))

    snap = service.get_snapshot(user_id="u1")

    assert snap.total_entries == 2
    assert {e.key for e in snap.active_entries} == {"language", "tone"}


def test_batch_snapshots_cover_every_requested_user() -> None:
    service = MemoryLongService(_Repo({"u1": [_entry("language")]}))

    snaps = service.get_snapshots_batch(user_ids=["u1", "u2"])

    assert set(snaps) == {"u1", "u2"}
    assert snaps["u1"].total_entries == 1
    assert snaps["u2"].total_entries == 0


def test_registry_plain_values_are_deny_by_default() -> None:
    registry = MemoryLongRegistry(
        allowed_keys={"language", "timezone"},
        allowed_plain_values={"language": {"fr", "en"}},
    )

    # None never needs the whitelist (opaque reference storage)
    assert registry.validate_value_plain(key="language", value=None) is True
    # whitelisted key + whitelisted value
    assert registry.validate_value_plain(key="language", value="fr") is True
    # whitelisted key, foreign value
    assert registry.validate_value_plain(key="language", value="klingon") is False
    # key with no plain-value whitelist at all
    assert registry.validate_value_plain(key="timezone", value="UTC") is False
    # and with an empty whitelist, everything non-None is refused
    empty = MemoryLongRegistry(allowed_keys={"language"})
    assert empty.validate_value_plain(key="language", value="fr") is False


def test_projector_emits_presence_flags_and_constraints_only() -> None:
    snapshot = MemoryLongSnapshot(
        active_entries=[
            _entry("language"),
            _entry("no_notifications"),
            _entry("no_tracking"),
        ],
        total_entries=3,
        revoked_entries=0,
        last_updated_at=None,
        created_at=utcnow(),
    )

    projected = MemoryLongContextProjector().project(snapshot)

    assert projected["preferences"] == {"language": True, "timezone": False}
    assert sorted(projected["constraints"]) == ["no_notifications", "no_tracking"]
    # ZKCS: nothing but declarative flags leaves the projector
    flat = str(projected)
    assert "value" not in flat and "payload" not in flat
