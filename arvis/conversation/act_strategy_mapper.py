# arvis/conversation/act_strategy_mapper.py

from arvis.linguistic.acts.act_types import LinguisticActType
from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.linguistic.acts.linguistic_act import LinguisticAct


def map_act_to_strategy(act: LinguisticActType) -> ResponseStrategyType:
    if act == LinguisticActType.ABSTENTION:
        return ResponseStrategyType.ABSTENTION

    if act == LinguisticActType.REQUEST_CONFIRMATION:
        return ResponseStrategyType.CONFIRMATION

    if act == LinguisticActType.DECISION:
        return ResponseStrategyType.ACTION

    return ResponseStrategyType.INFORMATIONAL


def map_strategy_to_act(strategy: ResponseStrategyType) -> LinguisticAct:
    """
    Convert a response strategy into a linguistic act.
    """

    if strategy == ResponseStrategyType.ABSTENTION:
        return LinguisticAct(LinguisticActType.ABSTENTION)

    if strategy == ResponseStrategyType.CONFIRMATION:
        return LinguisticAct(LinguisticActType.REQUEST_CONFIRMATION)

    if strategy == ResponseStrategyType.ACTION:
        return LinguisticAct(LinguisticActType.DECISION)

    return LinguisticAct(LinguisticActType.INFORMATION)
