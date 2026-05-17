# arvis/runtime/runtime_decision_record.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from arvis.types.identifiers import EntityID, deterministic_id


@dataclass(frozen=True)
class RuntimeDecisionRecord:
    decision_id: EntityID

    occurrence_id: EntityID

    tick: int

    selected_process_id: str | None

    rationale: str

    score: float | None

    causal_parent_id: EntityID | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        *,
        tick: int,
        selected_process_id: str | None,
        rationale: str,
        score: float | None,
        causal_parent_id: EntityID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RuntimeDecisionRecord:
        decision_id = EntityID(
            deterministic_id(
                "rtdec",
                tick,
                selected_process_id,
                rationale,
                score,
                causal_parent_id,
            )
        )

        occurrence_id = EntityID(f"rtocc-{uuid4().hex[:16]}")

        return RuntimeDecisionRecord(
            decision_id=decision_id,
            occurrence_id=occurrence_id,
            tick=tick,
            selected_process_id=selected_process_id,
            rationale=rationale,
            score=score,
            causal_parent_id=causal_parent_id,
            metadata=metadata or {},
        )
