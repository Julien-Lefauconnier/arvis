# arvis/reflexive/introspection/decision_introspector.py

from typing import Any


class DecisionIntrospector:
    """
    Explains the decision engine.
    """

    def describe(self) -> dict[str, Any]:
        return {
            "name": "decision_engine",
            "description": (
                "The decision engine routes user intents and proposes "
                "actions while respecting governance and uncertainty signals."
            ),
            "signals_used": [
                "prompt intent",
                "memory intent",
                "knowledge state",
                "uncertainty frames",
                "conversation mode",
            ],
            "guarantees": [
                "no raw user content analysis",
                "deterministic routing",
                "explicit uncertainty exposure",
            ],
        }
