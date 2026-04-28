# tests/timeline/test_timeline_fuzz.py

from hypothesis import given, strategies as st

from tests.timeline.helpers import make_entry

from arvis.timeline.timeline_hashchain import TimelineHashChain


@given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=50))
def test_hashchain_fuzz(ids):
    entries = [make_entry(i) for i in ids]

    chain = TimelineHashChain.build(entries)

    chain.verify(entries)
