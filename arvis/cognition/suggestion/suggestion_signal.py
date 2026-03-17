# arvis/cognition/suggestion/suggestion_signal.py

from dataclasses import dataclass


@dataclass(frozen=True)
class SuggestionSignal:
    """
    Declarative suggestion.
    """

    suggestion_type: str
    source: str