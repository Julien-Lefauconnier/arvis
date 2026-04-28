# arvis/linguistic/acts/act_types.py

from enum import StrEnum


class LinguisticActType(StrEnum):
    INFORMATION = "information"
    DECISION = "decision"
    REFUS = "refus"
    ABSTENTION = "abstention"
    REQUEST_CONFIRMATION = "request_confirmation"
    CAPABILITY_EXPLANATION = "capability_explanation"
