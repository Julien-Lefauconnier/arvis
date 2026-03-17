# tests/timeline/test_hashchain_large.py

from tests.timeline.helpers import make_entries
from arvis.timeline.timeline_hashchain import TimelineHashChain


def test_hashchain_large():

    entries = make_entries(1000)

    chain = TimelineHashChain.build(entries)

    assert len(chain.hashes) == 1000