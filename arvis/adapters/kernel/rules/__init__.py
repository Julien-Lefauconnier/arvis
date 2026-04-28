# arvis/adapters/kernel/rules/__init__.py

from .base_rule import CanonicalRule
from .decision_rules import DECISION_RULES
from .fallback_rules import FALLBACK_RULES
from .gate_rules import GATE_RULES
from .state_rules import STATE_RULES

ALL_RULES: tuple[CanonicalRule, ...] = (
    *STATE_RULES,
    *DECISION_RULES,
    *GATE_RULES,
    *FALLBACK_RULES,
)

__all__ = [
    "CanonicalRule",
    "STATE_RULES",
    "DECISION_RULES",
    "GATE_RULES",
    "FALLBACK_RULES",
    "ALL_RULES",
]
