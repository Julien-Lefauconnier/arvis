# arvis/reasoning/__init__.py
"""
Reasoning primitives.

Defines declarative reasoning intents and gap mappings.
"""

from .gap_to_intent_mapper import GapToIntentMapper
from .reasoning_gap import ReasoningGap
from .reasoning_intent import (
    ReasoningIntent,
    ReasoningIntentType,
)

__all__ = [
    "ReasoningIntent",
    "ReasoningIntentType",
    "GapToIntentMapper",
    "ReasoningGap",
]
