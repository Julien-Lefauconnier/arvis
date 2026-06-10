# tests/kernel/stages/test_bundle_stage_retrieval_snapshot.py
"""BundleStage: ZKCS-safe retrieval snapshot seam (ctx.extra channel)."""

from __future__ import annotations

from typing import Any

from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)
from arvis.kernel.pipeline.stages.bundle_stage import BundleStage


class _Ctx:
    """Minimal ctx stand-in for the BundleStage seam."""

    def __init__(self, extra: Any = None) -> None:
        self.introspection = None
        self.explanation = None
        self.timeline: list[Any] = []
        self.decision_layer = _DecisionLayer()
        if extra is not None:
            self.extra = extra


class _DecisionLayer:
    def __init__(self) -> None:
        self.decision_result = "DR"
        self.bundle: Any = None


class _CapturingBuilder:
    def __init__(self) -> None:
        self.kwargs: dict[str, Any] = {}

    def build(self, **kwargs: Any) -> str:
        self.kwargs = kwargs
        return "BUNDLE"


class _Pipeline:
    def __init__(self) -> None:
        self.bundle_builder = _CapturingBuilder()


def _snapshot() -> CognitiveRetrievalSnapshot:
    return CognitiveRetrievalSnapshot(
        source="qdrant",
        item_ids=["i1", "i2"],
        scores=[0.81, 0.74],
        semantic_roles=["facture", "assignation"],
        confidence=0.81,
    )


def test_retrieval_snapshot_absent_returns_none() -> None:
    assert BundleStage()._retrieval_snapshot(_Ctx()) is None


def test_retrieval_snapshot_non_dict_extra_returns_none() -> None:
    assert BundleStage()._retrieval_snapshot(_Ctx(extra="nope")) is None


def test_retrieval_snapshot_missing_key_returns_none() -> None:
    assert BundleStage()._retrieval_snapshot(_Ctx(extra={})) is None


def test_retrieval_snapshot_dict_value_rejected() -> None:
    # Pass-through only: the typed snapshot is the seam contract, not a dict.
    ctx = _Ctx(extra={"retrieval_snapshot": {"source": "x"}})
    assert BundleStage()._retrieval_snapshot(ctx) is None


def test_retrieval_snapshot_typed_passes_through_by_identity() -> None:
    snap = _snapshot()
    ctx = _Ctx(extra={"retrieval_snapshot": snap})
    assert BundleStage()._retrieval_snapshot(ctx) is snap


def test_run_forwards_snapshot_to_builder() -> None:
    snap = _snapshot()
    pipeline = _Pipeline()
    ctx = _Ctx(extra={"retrieval_snapshot": snap})

    BundleStage().run(pipeline, ctx)

    assert pipeline.bundle_builder.kwargs["retrieval_snapshot"] is snap
    assert ctx.decision_layer.bundle == "BUNDLE"


def test_run_forwards_none_when_absent() -> None:
    pipeline = _Pipeline()
    ctx = _Ctx()

    BundleStage().run(pipeline, ctx)

    assert pipeline.bundle_builder.kwargs["retrieval_snapshot"] is None
