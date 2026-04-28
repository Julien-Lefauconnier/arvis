# arvis/adapters/kernel/rules/state_rules.py

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .base_rule import CanonicalRule


class ProjectionValidRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        return getattr(ir, "state", None) is not None

    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "projection_valid"


class EarlyWarningDetectedRule(CanonicalRule):
    def applies(self, ir: Any) -> bool:
        state = getattr(ir, "state", None)
        if state is None:
            return False
        return bool(
            getattr(state, "stable", None) is False
            or getattr(state, "early_warning", False)
        )

    def emit_codes(self, ir: Any) -> Iterable[str]:
        yield "early_warning_detected"


STATE_RULES: tuple[CanonicalRule, ...] = (
    ProjectionValidRule(),
    EarlyWarningDetectedRule(),
)
