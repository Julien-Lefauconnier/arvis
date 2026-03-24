# tests/adapters/ir/test_decision_adapter.py

from __future__ import annotations

from enum import Enum
from types import SimpleNamespace

from arvis.adapters.ir.decision_adapter import DecisionIRAdapter


class DummyMemoryIntent(str, Enum):
    CANDIDATE = "candidate"


def test_decision_adapter_maps_decision_result_to_ir() -> None:
    action = SimpleNamespace(
        action_id="search_user_files",
        category="retrieval",
        parameters={"scope": "user"},
    )
    gap = SimpleNamespace(
        type="MISSING_CONTEXT",
        severity="high",
        description="missing target scope",
    )
    conflict = SimpleNamespace(
        type="MEMORY_VS_UNCERTAINTY",
        severity="high",
        description="memory candidate under uncertainty",
    )
    knowledge = SimpleNamespace(
        state="KNOWN",
        support_level=0.9,
    )
    uncertainty = SimpleNamespace(
        axis="temporal",
        level=0.25,
        explanation="time ambiguity",
    )

    result = SimpleNamespace(
        memory_intent=DummyMemoryIntent.CANDIDATE,
        proposed_actions=[action],
        reason="action_request|memory_pref:language",
        knowledge_snapshot=knowledge,
        conflicts=[conflict],
        gaps=[gap],
        reasoning_intents=["ask_confirmation"],
        uncertainty_frames=[uncertainty],
        context_hints={"preferred_language": "fr"},
    )

    ir = DecisionIRAdapter.from_result(result)

    assert ir.decision_kind == "action"
    assert ir.memory_intent == "candidate"
    assert ir.reason_codes == ("action_request", "memory_pref:language")
    assert len(ir.proposed_actions) == 1
    assert ir.proposed_actions[0].action_id == "search_user_files"
    assert ir.proposed_actions[0].severity == "safe"
    assert ir.gaps[0].gap_type == "MISSING_CONTEXT"
    assert ir.conflicts[0].conflict_type == "MEMORY_VS_UNCERTAINTY"
    assert ir.knowledge is not None
    assert ir.knowledge.state == "known"
    assert ir.uncertainty_frames[0].axis == "temporal"
    assert ir.context_hints["preferred_language"] == "fr"


def test_decision_adapter_detects_memory_kind_without_action_reason() -> None:
    result = SimpleNamespace(
        memory_intent=DummyMemoryIntent.CANDIDATE,
        proposed_actions=[],
        reason="explicit_memory_candidate",
        knowledge_snapshot=None,
        conflicts=[],
        gaps=[],
        reasoning_intents=[],
        uncertainty_frames=[],
        context_hints={},
    )

    ir = DecisionIRAdapter.from_result(result)

    assert ir.decision_kind == "memory"
    assert ir.memory_intent == "candidate"