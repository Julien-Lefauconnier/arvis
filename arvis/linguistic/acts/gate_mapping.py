# arvis/linguistic/acts/gate_mapping.py

from arvis.cognition.gate.cognitive_gate_verdict import (
    CognitiveGateVerdict,
)
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.acts.linguistic_act import LinguisticAct


def map_gate_verdict_to_act(
    *,
    verdict: CognitiveGateVerdict,
    has_decision: bool,
) -> LinguisticAct:
    """
    Deterministic mapping from cognitive gate verdict to linguistic act.

    Note:
    Authorization against ConversationMode is handled
    by the LinguisticActAuthorizationGate.
    """

    if verdict == CognitiveGateVerdict.ABSTAIN:
        return LinguisticAct(LinguisticActType.ABSTENTION)

    if verdict == CognitiveGateVerdict.REQUIRE_CONFIRMATION:
        return LinguisticAct(LinguisticActType.REQUEST_CONFIRMATION)

    if verdict == CognitiveGateVerdict.ALLOW:
        if has_decision:
            return LinguisticAct(LinguisticActType.DECISION)
        return LinguisticAct(LinguisticActType.INFORMATION)

    raise ValueError(f"Unsupported cognitive verdict: {verdict}")
