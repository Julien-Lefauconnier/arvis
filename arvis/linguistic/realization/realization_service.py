# arvis/linguistic/realization/realization_service.py

from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.linguistic.realization.default_templates import (
    DEFAULT_REALIZATION_TEMPLATES,
)


class LinguisticRealizationService:
    """
    Deterministic linguistic realization layer.

    Translates a LinguisticAct into a human-readable sentence.
    No generation. No LLM. No variability.
    """

    @staticmethod
    def realize(act: LinguisticAct) -> str:
        try:
            return DEFAULT_REALIZATION_TEMPLATES[act.act_type]
        except KeyError:
            return "Unable to produce an appropriate response."
