# arvis/adapters/kernel/rules/decision_rules.py

from __future__ import annotations

from typing import Any, Iterable

from .base_rule import CanonicalRule


class DecisionEmittedRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        return getattr(ir, "decision", None) is not None

    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "decision_emitted"


class ConflictDetectedRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        decision = getattr(ir, "decision", None)
        if decision is None:
            return False
        return bool(getattr(decision, "conflicts", ()))


    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "conflict_detected"


class UncertaintyDetectedRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        decision = getattr(ir, "decision", None)
        if decision is None:
            return False
        return bool(getattr(decision, "uncertainty_frames", ()))


    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "uncertainty_detected"


DECISION_RULES: tuple[CanonicalRule, ...] = (
    DecisionEmittedRule(),
    ConflictDetectedRule(),
    UncertaintyDetectedRule(),
)