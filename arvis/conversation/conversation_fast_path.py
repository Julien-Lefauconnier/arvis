# arvis/conversation/conversation_fast_path.py

from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.linguistic.realization.default_templates import (
    DEFAULT_REALIZATION_TEMPLATES,
)
from arvis.conversation.conversation_context import ConversationContext


class ConversationFastPath:
    """
    Minimal deterministic fast-path for ARVIS.

    Only handles simple template-based responses.
    """

    FAST_ACTS = {
        LinguisticActType.ABSTENTION,
        LinguisticActType.REQUEST_CONFIRMATION,
        LinguisticActType.CAPABILITY_EXPLANATION,
        LinguisticActType.REFUS,
    }

    @staticmethod
    def try_fast_path(context: ConversationContext) -> str | None:
        if context.act is None:
            return None

        act_type = context.act.act_type

        if act_type not in ConversationFastPath.FAST_ACTS:
            return None

        return DEFAULT_REALIZATION_TEMPLATES.get(act_type)