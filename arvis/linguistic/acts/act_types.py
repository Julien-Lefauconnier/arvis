# arvis/linguistic/acts/act_types.py

from enum import StrEnum


class LinguisticActType(StrEnum):
    """Linguistic act shaping a generation frame.

    Campaign SURFACE (DM-S5, 2026-09-02): REFUSAL was named REFUS
    (French, contrary to CONTRIBUTING's English-everywhere rule). The
    member was referenced nowhere and its value reaches no serialized
    or hashed payload (the prompt builder renders other members only),
    so both the name and the wire value are corrected.
    """

    INFORMATION = "information"
    DECISION = "decision"
    REFUSAL = "refusal"
    ABSTENTION = "abstention"
    REQUEST_CONFIRMATION = "request_confirmation"
    CAPABILITY_EXPLANATION = "capability_explanation"
