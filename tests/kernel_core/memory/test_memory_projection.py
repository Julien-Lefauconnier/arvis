# tests/kernel_core/memory/test_memory_projection.py

from datetime import datetime, timezone, timedelta

from arvis.kernel_core.memory.projection import project_memory
from veramem_kernel.journals.observation_long.observation_long_event import (
    ObservationLongEvent,
)


def _ts(dt: datetime) -> int:
    return int(dt.timestamp())


def _evt(
    *,
    user_id: str,
    namespace: str,
    key: str,
    op: str,
    value=None,
    tags=None,
    version=None,
    observed_at: datetime,
):
    payload = {
        "op": op,
        "namespace": namespace,
        "key": key,
    }

    if value is not None:
        payload["value"] = value

    if tags is not None:
        payload["tags"] = tags

    if version is not None:
        payload["version"] = version

    return ObservationLongEvent(
        user_id=user_id,
        source_type="memory",
        payload=payload,
        observed_at=observed_at,
    )


# =========================================================
# BASIC PUT
# =========================================================

def test_projection_put_creates_record():
    t0 = datetime.now(timezone.utc)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="fr",
            observed_at=t0,
        )
    ]

    state = project_memory(events)

    assert len(state) == 1

    record = list(state.values())[0]

    assert record.value == "fr"
    assert record.created_at == _ts(t0)
    assert record.updated_at == _ts(t0)
    assert record.status == "active"


# =========================================================
# CREATED_AT INVARIANT
# =========================================================

def test_projection_preserves_created_at_on_update():
    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(seconds=10)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="fr",
            observed_at=t0,
        ),
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="en",
            observed_at=t1,
        ),
    ]

    state = project_memory(events)
    record = list(state.values())[0]

    assert record.value == "en"
    assert record.created_at == _ts(t0)  # invariant
    assert record.updated_at == _ts(t1)


# =========================================================
# DELETE
# =========================================================

def test_projection_delete_marks_record_deleted():
    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(seconds=5)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="fr",
            observed_at=t0,
        ),
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="delete",
            observed_at=t1,
        ),
    ]

    state = project_memory(events)
    record = list(state.values())[0]

    assert record.status == "deleted"
    assert record.created_at == _ts(t0)
    assert record.updated_at == _ts(t1)


# =========================================================
# DELETE NON-EXISTENT (NO CRASH)
# =========================================================

def test_projection_delete_nonexistent_is_noop():
    t0 = datetime.now(timezone.utc)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="delete",
            observed_at=t0,
        )
    ]

    state = project_memory(events)

    assert state == {}


# =========================================================
# RECORD ID STABILITY
# =========================================================

def test_projection_record_id_stable_across_updates():
    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(seconds=10)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="fr",
            observed_at=t0,
        ),
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="en",
            observed_at=t1,
        ),
    ]

    state = project_memory(events)
    record = list(state.values())[0]

    assert record.record_id == "mem:u1:pref:lang"


# =========================================================
# DETERMINISM
# =========================================================

def test_projection_is_deterministic():
    t0 = datetime.now(timezone.utc)
    t1 = t0 + timedelta(seconds=10)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="fr",
            observed_at=t0,
        ),
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="en",
            observed_at=t1,
        ),
    ]

    state1 = project_memory(events)
    state2 = project_memory(events)

    assert state1 == state2


# =========================================================
# MULTI KEYS ISOLATION
# =========================================================

def test_projection_isolates_multiple_keys():
    t0 = datetime.now(timezone.utc)

    events = [
        _evt(
            user_id="u1",
            namespace="pref",
            key="lang",
            op="put",
            value="fr",
            observed_at=t0,
        ),
        _evt(
            user_id="u1",
            namespace="pref",
            key="timezone",
            op="put",
            value="UTC",
            observed_at=t0,
        ),
    ]

    state = project_memory(events)

    assert len(state) == 2

    keys = {k[2] for k in state.keys()}
    assert keys == {"lang", "timezone"}