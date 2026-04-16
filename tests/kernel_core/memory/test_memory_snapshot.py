# tests/kernel_core/memory/test_memory_snapshot.py

from arvis.kernel_core.memory.repositories.in_memory import InMemoryMemoryRepository
from arvis.kernel_core.memory.service import MemoryService


def test_get_snapshot_empty():
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo=repo)

    snapshot = service.get_snapshot(user_id="u1")

    assert snapshot.user_id == "u1"
    assert snapshot.records == ()
    assert snapshot.total_records == 0
    assert snapshot.active_records == 0
    assert snapshot.deleted_records == 0
    assert snapshot.last_updated_at is None
    assert snapshot.is_empty is True


def test_get_snapshot_returns_deterministic_records():
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo=repo)

    service.put_record(user_id="u1", namespace="prefs", key="language", value="fr")
    service.put_record(user_id="u1", namespace="prefs", key="timezone", value="Europe/Paris")

    snapshot = service.get_snapshot(user_id="u1")

    assert snapshot.user_id == "u1"
    assert snapshot.total_records == 2
    assert snapshot.active_records == 2
    assert snapshot.deleted_records == 0
    assert snapshot.is_empty is False

    keys = [(r.namespace, r.key) for r in snapshot.records]
    assert keys == sorted(keys)


def test_get_snapshot_namespace_filter():
    repo = InMemoryMemoryRepository()
    service = MemoryService(repo=repo)

    service.put_record(user_id="u1", namespace="prefs", key="language", value="fr")
    service.put_record(user_id="u1", namespace="profile", key="name", value="Julien")

    snapshot = service.get_snapshot(user_id="u1", namespace="prefs")

    assert snapshot.total_records == 1
    assert len(snapshot.records) == 1
    assert snapshot.records[0].namespace == "prefs"
    assert snapshot.records[0].key == "language"