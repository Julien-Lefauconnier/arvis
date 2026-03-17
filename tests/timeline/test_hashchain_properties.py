# tests/timeline/test_hashchain_properties.py

from hypothesis import given, strategies as st

from tests.timeline.helpers import make_entry
from arvis.timeline.timeline_hashchain import TimelineHashChain


@given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=20))
def test_hashchain_incremental_equals_build(ids):

    entries = [make_entry(i) for i in ids]

    batch = TimelineHashChain.build(entries)

    chain = TimelineHashChain(())

    for e in entries:
        chain = chain.append(e)

    assert chain.hashes == batch.hashes