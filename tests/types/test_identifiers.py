# tests/types/test_identifiers.py

from arvis.types.identifiers import EntityID, MemoryKey, TimelineID


def test_entity_id_is_string():

    eid = EntityID("entity-1")

    assert isinstance(eid, str)
    assert eid == "entity-1"


def test_memory_key_is_string():

    key = MemoryKey("memory-abc")

    assert isinstance(key, str)
    assert key == "memory-abc"


def test_timeline_id_is_string():

    tid = TimelineID("timeline-42")

    assert isinstance(tid, str)
    assert tid == "timeline-42"