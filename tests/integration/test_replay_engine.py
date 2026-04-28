# tests/integration/test_replay_engine.py

from arvis.kernel.replay_engine import ReplayEngine
from arvis.timeline.timeline_hashchain import TimelineHashChain
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from tests.timeline.helpers import make_entries


def make_snapshot(n):
    entries = make_entries(n)

    chain = TimelineHashChain.build(entries)

    return TimelineSnapshot(tuple(entries), chain)


def test_replay_engine_basic():
    engine = ReplayEngine()

    snapshots = [
        make_snapshot(2),
        make_snapshot(3),
        make_snapshot(4),
    ]

    bundles = engine.replay(snapshots)

    assert len(bundles) == 3


def test_replay_is_deterministic():
    engine = ReplayEngine()

    snapshots = [
        make_snapshot(3),
        make_snapshot(5),
    ]

    run1 = engine.replay(snapshots)
    run2 = engine.replay(snapshots)

    assert run1 == run2


def test_replay_preserves_sequence_length():
    engine = ReplayEngine()

    snapshots = [make_snapshot(i) for i in range(2, 8)]

    bundles = engine.replay(snapshots)

    assert len(bundles) == len(snapshots)
