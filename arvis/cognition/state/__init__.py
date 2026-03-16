# arvis/cognition/state/__init__.py

"""
Cognitive state primitives.

Defines the unified cognitive state representation used
by the ARVIS kernel.
"""

from .cognitive_state import (
    CognitiveState,
    CognitiveRiskSnapshot,
)

__all__ = [
    "CognitiveState",
    "CognitiveRiskSnapshot",
]