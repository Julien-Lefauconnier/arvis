# tests/runtime/test_runtime_decision_record.py

from __future__ import annotations

from arvis.runtime.runtime_decision_record import RuntimeDecisionRecord


def test_runtime_decision_record_separates_logical_and_runtime_identity():
    r1 = RuntimeDecisionRecord.create(
        tick=1,
        selected_process_id="p1",
        rationale="test",
        score=1.0,
    )

    r2 = RuntimeDecisionRecord.create(
        tick=1,
        selected_process_id="p1",
        rationale="test",
        score=1.0,
    )

    assert r1.decision_id == r2.decision_id
    assert r1.occurrence_id != r2.occurrence_id


def test_runtime_decision_record_preserves_fields():
    record = RuntimeDecisionRecord.create(
        tick=42,
        selected_process_id="p-test",
        rationale="highest scheduling score",
        score=12.5,
        causal_parent_id="parent",
        metadata={"k": "v"},
    )

    assert record.tick == 42
    assert record.selected_process_id == "p-test"
    assert record.score == 12.5
    assert record.causal_parent_id == "parent"
    assert record.metadata["k"] == "v"
