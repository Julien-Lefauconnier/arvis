# arvis/kernel_core/memory/projection.py

from collections.abc import Iterable

from arvis.kernel_core.memory.models import MemoryRecord
from arvis.kernel_core.memory.observation_long_event import (
    ObservationLongEvent,
)


def project_memory(
    events: Iterable["ObservationLongEvent"],
) -> dict[tuple[str, str, str], MemoryRecord]:
    """
    Pure projection:
    ObservationLongEvent -> MemoryRecord state

    Guarantees:
    - deterministic replay
    - stable record identity
    - immutable state reconstruction
    """

    state: dict[tuple[str, str, str], MemoryRecord] = {}

    for evt in events:
        if evt.source_type != "memory":
            continue

        payload = evt.payload
        namespace = payload["namespace"]
        key = payload["key"]
        op = payload["op"]

        key_tuple = (evt.user_id, namespace, key)
        ts = int(evt.observed_at.timestamp())

        if op == "put":
            existing = state.get(key_tuple)

            created_at = existing.created_at if existing is not None else ts
            record_id = (
                existing.record_id
                if existing is not None
                else f"mem:{evt.user_id}:{namespace}:{key}"
            )

            state[key_tuple] = MemoryRecord(
                record_id=record_id,
                user_id=evt.user_id,
                namespace=namespace,
                key=key,
                value=payload["value"],
                created_at=created_at,
                updated_at=ts,
                version=payload.get(
                    "version",
                    existing.version + 1 if existing is not None else 1,
                ),
                tags=tuple(payload.get("tags", [])),
                status="active",
            )

        elif op == "delete":
            existing = state.get(key_tuple)
            if existing is None:
                continue

            state[key_tuple] = MemoryRecord(
                record_id=existing.record_id,
                user_id=existing.user_id,
                namespace=existing.namespace,
                key=existing.key,
                value=existing.value,
                created_at=existing.created_at,
                updated_at=ts,
                version=existing.version,
                tags=existing.tags,
                status="deleted",
            )

    return state
