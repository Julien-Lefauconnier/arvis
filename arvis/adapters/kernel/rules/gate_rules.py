# arvis/adapters/kernel/rules/gate_rules.py

from __future__ import annotations

from typing import Any, Iterable

from .base_rule import CanonicalRule


class GateVerdictRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        gate = getattr(ir, "gate", None)
        return gate is not None and getattr(gate, "verdict", None) is not None

    def emit_codes(self, ir: Any) -> Iterable[str]:
        gate = getattr(ir, "gate", None)
        verdict = getattr(getattr(gate, "verdict", None), "value", None)
        if verdict:
            yield f"gate_{verdict}"


class GateInstabilityDetectedRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        gate = getattr(ir, "gate", None)
        if gate is None:
            return False
        instability_score = getattr(gate, "instability_score", None)
        return instability_score is not None and instability_score > 0.7

    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "instability_detected"


GATE_RULES: tuple[CanonicalRule, ...] = (
    GateVerdictRule(),
    GateInstabilityDetectedRule(),
)
