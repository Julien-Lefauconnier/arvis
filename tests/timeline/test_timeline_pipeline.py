# tests/timeline/test_timeline_pipeline.py

from arvis.timeline.timeline_delta import TimelineDelta
from arvis.timeline.timeline_hashchain import TimelineHashChain
from arvis.timeline.timeline_snapshot import TimelineSnapshot
from tests.timeline.helpers import make_entries


def test_full_timeline_pipeline():
    entries = make_entries(8)

    base_entries = tuple(entries[:4])
    target_entries = tuple(entries)

    base_chain = TimelineHashChain.build(base_entries)
    target_chain = TimelineHashChain.build(target_entries)

    base = TimelineSnapshot(base_entries, base_chain)
    target = TimelineSnapshot(target_entries, target_chain)

    delta = TimelineDelta.from_snapshots(base, target)

    replay = delta.apply_to(base)

    assert replay == target

    target_chain.verify(target.entries)
