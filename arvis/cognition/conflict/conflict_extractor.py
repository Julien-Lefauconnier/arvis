# arvis/cognition/conflict/conflict_extractor.py

from typing import Any

from .conflict_signal import ConflictSignal
from .conflict_type import REASON_MISMATCH


def extract_conflicts_from_bundle(bundle: Any) -> list[ConflictSignal]:
    """
    Minimal conflict extraction (safe baseline).
    """

    conflicts: list[ConflictSignal] = []

    # Exemple simple : incohérence décision / explication
    decision_reason = getattr(bundle, "decision_reason", None)
    explanation = getattr(bundle, "explanation", None)

    if decision_reason is not None and explanation is not None:
        try:
            decision_str = str(decision_reason)
            explanation_str = str(explanation)
        except Exception:
            return conflicts

        if decision_str and decision_str not in explanation_str:
            conflicts.append(
                ConflictSignal(
                    REASON_MISMATCH,
                    {"reason": "reason_mismatch", "severity": 0.5},
                )
            )

    return conflicts
