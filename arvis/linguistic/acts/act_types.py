# arvis/linguistic/acts/act_types.py

from enum import Enum


class LinguisticActType(str, Enum):
    INFORMATION = "information"
    DECISION = "decision"
    REFUS = "refus"
    ABSTENTION = "abstention"
    REQUEST_CONFIRMATION = "request_confirmation"
    CAPABILITY_EXPLANATION = "capability_explanation"
