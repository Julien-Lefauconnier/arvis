# arvis/linguistic/acts/act_authorization_gate.py

from arvis.linguistic.acts.linguistic_act import LinguisticAct
from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.acts.mode_act_policy import MODE_ACT_POLICY
from arvis.cognition.conversation.conversation_mode import ConversationMode


class LinguisticActAuthorizationGate:
    """
    A3 — Linguistic Act Authorization Gate.

    Validates whether a linguistic act may be expressed
    under the resolved ConversationMode.

    This gate:
    - never decides
    - never reformulates
    - never calls the LLM
    """

    @staticmethod
    def authorize(*, mode: ConversationMode, act: LinguisticAct) -> LinguisticAct:
        allowed: set[LinguisticActType] = MODE_ACT_POLICY.get(mode, set())

        if act.act_type in allowed:
            return act

        # ARVIS invariant: abstention is the only valid fallback
        return LinguisticAct(
            LinguisticActType.ABSTENTION,
        )
