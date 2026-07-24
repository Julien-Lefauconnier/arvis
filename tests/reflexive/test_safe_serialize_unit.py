# tests/reflexive/test_safe_serialize_unit.py

"""Unit contract of ReflexiveSnapshot._safe_serialize (A14-P1-01).

The a14 audit probe: a plain dataclass tree (the real CognitiveState
shape) must serialize; before the fix it travelled as a live object and
the attestation's json.dumps raised, silently degrading reflexive to
None. Live objects with no serialization contract surface as a
deterministic opaque marker, never as an exception.
"""

import dataclasses
import datetime
import enum
import json
import threading

from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot


class _Mode(enum.Enum):
    FAST = "fast"


@dataclasses.dataclass
class _Inner:
    values: tuple[int, ...] = (1, 2)
    mode: _Mode = _Mode.FAST


@dataclasses.dataclass
class _State:
    x: int = 1
    inner: _Inner = dataclasses.field(default_factory=_Inner)
    when: datetime.datetime = dataclasses.field(
        default_factory=lambda: datetime.datetime(2026, 7, 24, 12, 0, 0)
    )


def _snapshot() -> ReflexiveSnapshot:
    return ReflexiveSnapshot(
        capabilities=None,
        cognitive_state=None,
        timeline_views={},
        introspection=None,
        generated_at=datetime.datetime(2026, 7, 24, 12, 0, 0),
    )


def test_audit_probe_dataclass_tree_serializes() -> None:
    serialized = _snapshot()._safe_serialize(_State())
    assert serialized == {
        "x": 1,
        "inner": {"values": [1, 2], "mode": "fast"},
        "when": "2026-07-24T12:00:00",
    }
    json.dumps(serialized)  # attestation-compatible by construction


class _Journal:
    def __init__(self) -> None:
        self.lock = threading.Lock()


def test_live_object_surfaces_as_deterministic_opaque_marker() -> None:
    serialized = _snapshot()._safe_serialize({"timeline": _Journal()})
    assert serialized == {"timeline": "<unserialized:_Journal>"}
    json.dumps(serialized)
