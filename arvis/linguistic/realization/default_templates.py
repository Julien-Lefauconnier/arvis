# arvis/linguistic/realization/default_templates.py

from arvis.linguistic.acts.act_types import LinguisticActType

DEFAULT_REALIZATION_TEMPLATES: dict[LinguisticActType, str] = {
    LinguisticActType.INFORMATION:
        "Here is the available information.",

    LinguisticActType.DECISION:
        "Here is the decision.",

    LinguisticActType.REFUS:
        "This action cannot be executed.",

    LinguisticActType.ABSTENTION:
        "I do not have enough information to decide.",

    LinguisticActType.REQUEST_CONFIRMATION:
        "This request is ambiguous. Could you clarify what you want to do?",

    LinguisticActType.CAPABILITY_EXPLANATION:
        "I can explain how I work and what my capabilities are.",
}