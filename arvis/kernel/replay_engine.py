# arvis/kernel/replay_engine.py

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.ir.cognitive_ir import CognitiveIR
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.timeline.timeline_snapshot import TimelineSnapshot


@dataclass
class ReplayEngine:
    """
    Deterministic replay engine.

    Reconstructs the sequence of cognitive bundles produced
    from a sequence of timeline snapshots.
    Extended capabilities:
    - timeline replay (original behavior)
    - IR replay (canonical CognitiveOS replay)
    """

    # -----------------------------------------------------
    # TIMELINE REPLAY (legacy / bundle reconstruction)
    # -----------------------------------------------------
    def replay(
        self,
        timeline_snapshots: Iterable[TimelineSnapshot],
    ) -> list[CognitiveBundleSnapshot]:
        bundles: list[CognitiveBundleSnapshot] = []

        for snap in timeline_snapshots:
            bundle = CognitiveBundleBuilder.from_timeline(snap)

            bundles.append(bundle)

        return bundles

    # -----------------------------------------------------
    # IR REPLAY (canonical CognitiveOS path)
    # -----------------------------------------------------
    def replay_ir(
        self,
        ir: CognitiveIR,
        *,
        pipeline: CognitivePipeline | None = None,
    ) -> Any:
        """
        Replay full cognitive execution from IR.

        This is the canonical deterministic replay path used by CognitiveOS.
        """

        pipeline = pipeline or CognitivePipeline()

        return pipeline.run_from_ir(ir)

    # -----------------------------------------------------
    # AUTO REPLAY (smart dispatch)
    # -----------------------------------------------------
    def replay_auto(
        self,
        data: Any,
        *,
        pipeline: CognitivePipeline | None = None,
    ) -> Any:
        """
        Smart replay dispatcher:
        - list[TimelineSnapshot] → timeline replay
        - CognitiveIR → IR replay
        """

        if isinstance(data, list):
            return self.replay(data)

        if isinstance(data, CognitiveIR):
            return self.replay_ir(data, pipeline=pipeline)

        raise TypeError(f"Unsupported replay input type: {type(data)}")
