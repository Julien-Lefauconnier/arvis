# arvis/linguistic/acts/mode_act_policy.py

from arvis.cognition.conversation.conversation_mode import ConversationMode
from arvis.linguistic.acts.act_types import LinguisticActType

"""
Declarative mapping between ConversationMode and authorized LinguisticActType.

Invariants:
- ABSTENTION is always authorized.
- Any act not explicitly listed is forbidden.
- No reasoning, no fallback logic, no LLM access.
"""

MODE_ACT_POLICY: dict[ConversationMode, set[LinguisticActType]] = {
    ConversationMode.DEFAULT: {
        LinguisticActType.INFORMATION,
        LinguisticActType.REQUEST_CONFIRMATION,
        LinguisticActType.ABSTENTION,
    },
    ConversationMode.AUDIT: {
        LinguisticActType.INFORMATION,
        LinguisticActType.ABSTENTION,
    },
    ConversationMode.GOVERNANCE: {
        LinguisticActType.INFORMATION,
        LinguisticActType.DECISION,
        LinguisticActType.ABSTENTION,
    },
    ConversationMode.RESTRICTED: {
        LinguisticActType.ABSTENTION,
    },
}
