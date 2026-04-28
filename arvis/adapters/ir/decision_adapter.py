# arvis/adapters/ir/decision_adapter.py

from __future__ import annotations

from typing import Any, Dict
from hashlib import sha256
from json import dumps

from arvis.ir.decision import (
    CognitiveActionIR,
    CognitiveConflictIR,
    CognitiveDecisionIR,
    CognitiveGapIR,
    CognitiveKnowledgeIR,
    CognitiveUncertaintyIR,
)


def _hash(payload: Dict[str, Any]) -> str:
    return sha256(dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _string_value(value: object | None, default: str = "") -> str:
    if value is None:
        return default
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, str):
        return enum_value
    return str(value)


def _normalize_reason_codes(value: object | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(x).strip() for x in value if str(x).strip())
    raw = str(value)
    return tuple(part.strip() for part in raw.split("|") if part.strip())


class DecisionIRAdapter:
    @staticmethod
    def from_result(result: object) -> CognitiveDecisionIR:
        reason_codes = _normalize_reason_codes(
            getattr(result, "reason_codes", None) or getattr(result, "reason", None)
        )

        actions = tuple(
            CognitiveActionIR(
                action_id=str(getattr(a, "action_id", "unknown")),
                category=str(getattr(a, "category", "unknown")),
                severity=DecisionIRAdapter._severity(a),
                requires_confirmation=DecisionIRAdapter._severity(a) != "safe",
                parameters=getattr(a, "parameters", {}) or {},
            )
            for a in (getattr(result, "proposed_actions", []) or [])
        )

        gaps = tuple(
            CognitiveGapIR(
                gap_type=_string_value(getattr(g, "type", None), "unknown"),
                severity=_string_value(getattr(g, "severity", None), "medium"),
                description=str(getattr(g, "description", "")),
            )
            for g in (getattr(result, "gaps", []) or [])
        )

        conflicts = tuple(
            CognitiveConflictIR(
                conflict_type=_string_value(getattr(c, "type", None), "unknown"),
                severity=_string_value(getattr(c, "severity", None), "high"),
                description=str(getattr(c, "description", "")),
                resolvable_by_confirmation=bool(
                    getattr(c, "resolvable_by_confirmation", True)
                ),
            )
            for c in (getattr(result, "conflicts", []) or [])
        )

        knowledge_snapshot = getattr(result, "knowledge_snapshot", None)
        knowledge = None
        if knowledge_snapshot is not None:
            knowledge = CognitiveKnowledgeIR(
                state=_string_value(
                    getattr(knowledge_snapshot, "state", None), "unknown"
                ).lower(),
                support_level=getattr(knowledge_snapshot, "support_level", None),
            )

        uncertainty = tuple(
            CognitiveUncertaintyIR(
                axis=_string_value(getattr(u, "axis", None), "epistemic"),
                level=float(getattr(u, "level", 0.5)),
                explanation=getattr(u, "explanation", None),
            )
            for u in (getattr(result, "uncertainty_frames", []) or [])
        )

        memory_intent = _string_value(
            getattr(result, "memory_intent", None), "none"
        ).lower()

        payload = {
            "reason_codes": reason_codes,
            "memory_intent": memory_intent,
            "actions": [a.action_id for a in actions],
            "gaps": [g.gap_type for g in gaps],
            "conflicts": [c.conflict_type for c in conflicts],
        }

        return CognitiveDecisionIR(
            decision_id=_hash(payload),
            decision_kind=DecisionIRAdapter._kind(reason_codes, memory_intent),
            memory_intent=memory_intent,
            reason_codes=reason_codes,
            proposed_actions=actions,
            gaps=gaps,
            conflicts=conflicts,
            reasoning_intents=tuple(
                _string_value(x)
                for x in (getattr(result, "reasoning_intents", []) or [])
            ),
            uncertainty_frames=uncertainty,
            knowledge=knowledge,
            context_hints=getattr(result, "context_hints", {}) or {},
        )

    @staticmethod
    def _kind(reason_codes: tuple[str, ...], memory_intent: str) -> str:
        tokens = set(reason_codes)

        if "action_request" in tokens:
            return "action"
        if "search_user_files" in tokens:
            return "action"
        if memory_intent not in {"", "none"}:
            return "memory"
        if "conversation" in tokens:
            return "conversational"
        if "informational_query" in tokens:
            return "informational"
        if "meta_query" in tokens:
            return "meta"
        return "unknown"

    @staticmethod
    def _severity(action: object) -> str:
        action_id = str(getattr(action, "action_id", ""))

        if action_id in {"search_user_files", "retrieve", "summarize"}:
            return "safe"
        if action_id == "memory_store":
            return "confirm"
        return "confirm"
