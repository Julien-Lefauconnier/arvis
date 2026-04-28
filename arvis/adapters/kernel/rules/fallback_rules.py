# arvis/adapters/kernel/rules/fallback_rules.py

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .base_rule import CanonicalRule


class GhostSignalFallbackRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        has_state = getattr(ir, "state", None) is not None
        has_decision = getattr(ir, "decision", None) is not None
        has_gate = getattr(ir, "gate", None) is not None
        return not (has_state or has_decision or has_gate)

    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "ghost_signal"


FALLBACK_RULES: tuple[CanonicalRule, ...] = (GhostSignalFallbackRule(),)
