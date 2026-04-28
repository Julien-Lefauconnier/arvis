# tests/kernel_core/memory/test_memory_long_adapter.py

from datetime import UTC, datetime

from arvis.kernel_core.memory.adapters.memory_long_adapter import (
    to_memory_long_entry,
)
from arvis.kernel_core.memory.models import MemoryRecord
from arvis.memory.memory_long_entry import MemoryLongType


def _record(**overrides):
    base = dict(
        record_id="mem:u1:pref:lang",
        user_id="u1",
        namespace="pref",
        key="language",
        value="fr",
        created_at=1000,
        updated_at=1000,
        version=1,
        tags=(),
        status="active",
    )

    base.update(overrides)

    return MemoryRecord(**base)


# =========================================================
# BASIC ADAPTATION
# =========================================================


def test_adapter_creates_entry():
    record = _record()

    entry = to_memory_long_entry(record)

    assert entry is not None
    assert entry.key == "language"
    assert entry.memory_type == MemoryLongType.PREFERENCE


# =========================================================
# NO PAYLOAD LEAK
# =========================================================


def test_adapter_does_not_expose_value():
    record = _record(value="SECRET")

    entry = to_memory_long_entry(record)

    assert not hasattr(entry, "value")


# =========================================================
# VALUE REF STABILITY
# =========================================================


def test_value_ref_stable():
    record = _record(version=3)

    entry = to_memory_long_entry(record)

    assert entry.value_ref == "mem:u1:pref:lang:v3"


# =========================================================
# CREATED_AT CONVERSION
# =========================================================


def test_created_at_is_datetime():
    record = _record(created_at=1000)

    entry = to_memory_long_entry(record)

    assert isinstance(entry.created_at, datetime)
    assert entry.created_at.tzinfo == UTC


# =========================================================
# DELETED RECORD FILTERED
# =========================================================


def test_deleted_record_returns_none():
    record = _record(status="deleted")

    entry = to_memory_long_entry(record)

    assert entry is None


# =========================================================
# CONSTRAINT DETECTION
# =========================================================


def test_constraint_key_detection():
    record = _record(namespace="misc", key="no_tracking")

    entry = to_memory_long_entry(record)

    assert entry.memory_type == MemoryLongType.CONSTRAINT
