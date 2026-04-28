# tests/memory/test_memory_long_snapshot.py

from arvis.memory.memory_long_snapshot import MemoryLongSnapshot


def test_memory_long_snapshot_creation():
    snap = MemoryLongSnapshot()

    assert snap is not None
