# arvis/linguistic/generation/frame_builder.py

from typing import Any, Dict, Optional

from arvis.linguistic.generation.generation_frame import (
    LinguisticGenerationFrame,
)
from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot
from arvis.linguistic.acts.act_types import LinguisticActType


# Canonical expressions associated with each linguistic act
# These are protected tokens that must NOT leak across acts
_ACT_CANONICALS = {
    LinguisticActType.INFORMATION: {"Available information"},
    LinguisticActType.DECISION: {"Decision"},
    LinguisticActType.REFUS: {"Action refused"},
    LinguisticActType.ABSTENTION: {"Unable to decide"},
    LinguisticActType.REQUEST_CONFIRMATION: {"Confirmation required"},
}


def build_generation_frame(
    *,
    act: LinguisticAct,
    lexicon: LexiconSnapshot,
    state: Optional[Any] = None,
) -> LinguisticGenerationFrame:
    """
    Build a constrained linguistic generation frame.

    Rules:
    - Keep ALL preferred lexicon entries
    - EXCEPT: remove canonical expressions tied to other acts
      (prevents semantic leakage across acts)
    - Domain-specific entries are NEVER filtered out
    """

    # --------------------------------------------
    # Canonical filtering
    # --------------------------------------------
    allowed_act_canonicals = _ACT_CANONICALS.get(act.act_type, set())
    all_act_canonicals = set().union(*_ACT_CANONICALS.values())
    forbidden_act_canonicals = all_act_canonicals - allowed_act_canonicals

    allowed = [
        e.canonical_form
        for e in lexicon.entries
        if e.status == "preferred" and e.canonical_form not in forbidden_act_canonicals
    ]

    # --------------------------------------------
    # Default tone / verbosity
    # --------------------------------------------
    tone = "neutral"
    verbosity = "minimal"

    constraints = []
    preferences = {}

    # --------------------------------------------
    # Adaptive behavior (state-driven)
    # --------------------------------------------
    signals: Dict[str, Any] = {}

    if state is not None and hasattr(state, "signals"):
        raw_signals = state.signals
        if isinstance(raw_signals, dict):
            signals = raw_signals

        instability = signals.get("instability", 0.0)
        memory_instability = signals.get("memory_instability", 0.0)

        # ----------------------------------
        # Adaptive tone
        # ----------------------------------
        if instability > 0.6:
            tone = "cautious"
        elif memory_instability > 0.6:
            tone = "reflective"

        # ----------------------------------
        # Adaptive verbosity
        # ----------------------------------
        if instability > 0.5:
            verbosity = "low"
        elif memory_instability > 0.5:
            verbosity = "medium"

        # ----------------------------------
        # Memory signals injection
        # ----------------------------------
        constraints = signals.get("constraints", [])
        preferences = signals.get("preferences", {})

    return LinguisticGenerationFrame(
        act=act.act_type,
        allowed_entries=allowed,
        tone=tone,
        verbosity=verbosity,
        constraints=constraints,
        preferences=preferences,
    )
