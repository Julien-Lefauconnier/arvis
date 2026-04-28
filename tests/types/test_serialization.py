# tests/types/test_serialization.py

import pickle

from arvis.timeline.timeline_hashchain import TimelineHashChain
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from tests.timeline.helpers import make_entries


def test_snapshot_pickle_roundtrip():
    entries = tuple(make_entries(3))

    chain = TimelineHashChain.build(entries)

    snap = TimelineSnapshot(entries, chain)

    data = pickle.dumps(snap)

    restored = pickle.loads(data)

    assert restored == snap
