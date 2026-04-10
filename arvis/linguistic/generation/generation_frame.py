# arvis/linguistic/generation/generation_frame.py

from dataclasses import dataclass
from typing import Dict, Optional
from arvis.linguistic.acts.act_types import LinguisticActType


@dataclass(frozen=True)
class LinguisticGenerationFrame:
    """
    Constrained linguistic frame passed to the LLM.

    This object defines HOW something may be expressed,
    never WHAT should be decided.
    """

    act: LinguisticActType
    allowed_entries: list[str]
    tone: str = "neutral"
    verbosity: str = "minimal"
    allow_speculation: bool = False
    constraints: list[str] | None = None
    preferences: Optional[Dict[str, object]] = None
