# tests/perf/test_hashchain_perf.py

from tests.timeline.helpers import make_entries
from arvis.timeline.timeline_hashchain import TimelineHashChain


def test_hashchain_build_perf(benchmark):
    entries = make_entries(5000)

    benchmark(lambda: TimelineHashChain.build(entries))
