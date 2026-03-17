# arvis/kernel/replay_engine.py

from dataclasses import dataclass
from typing import Iterable, List

from arvis.timeline.timeline_snapshot import TimelineSnapshot
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot


@dataclass
class ReplayEngine:
    """
    Deterministic replay engine.

    Reconstructs the sequence of cognitive bundles produced
    from a sequence of timeline snapshots.
    """

    def replay(
        self,
        timeline_snapshots: Iterable[TimelineSnapshot],
    ) -> List[CognitiveBundleSnapshot]:

        bundles: List[CognitiveBundleSnapshot] = []

        for snap in timeline_snapshots:

            bundle = CognitiveBundleBuilder.from_timeline(snap)

            bundles.append(bundle)

        return bundles