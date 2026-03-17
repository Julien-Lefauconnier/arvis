# tests/timeline/test_delta_properties.py

from hypothesis import given, strategies as st

from tests.timeline.helpers import make_entries

from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.timeline.timeline_delta import TimelineDelta
from arvis.timeline.timeline_hashchain import TimelineHashChain


@given(st.integers(min_value=2, max_value=20))
def test_delta_replay_invariant(n):

    entries = make_entries(n)

    mid = n // 2

    base_entries = tuple(entries[:mid])
    target_entries = tuple(entries)

    base_chain = TimelineHashChain.build(base_entries)
    target_chain = TimelineHashChain.build(target_entries)

    base = TimelineSnapshot(base_entries, base_chain)
    target = TimelineSnapshot(target_entries, target_chain)

    delta = TimelineDelta.from_snapshots(base, target)

    replay = delta.apply_to(base)

    assert replay == target