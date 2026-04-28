# tests/cognition/policy/test_cognitive_signal_snapshot.py

import pytest

from arvis.cognition.policy import CognitiveSignalSnapshot


def test_signal_snapshot_creation():
    s = CognitiveSignalSnapshot(
        signal_id="s1",
        signal_type="memory",
        source="timeline",
        timestamp=10,
    )

    assert s.signal_id == "s1"


def test_signal_snapshot_to_dict():
    s = CognitiveSignalSnapshot(
        signal_id="s1",
        signal_type="memory",
        source="timeline",
        timestamp=10,
    )

    d = s.to_dict()

    assert d["signal_type"] == "memory"


def test_signal_snapshot_immutable():
    s = CognitiveSignalSnapshot("a", "b", "c", 1)

    with pytest.raises(AttributeError):
        s.timestamp = 10
