# tests/conversation/test_act_strategy_mapper.py

from arvis.cognition.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.act_strategy_mapper import map_act_to_strategy
from arvis.linguistic.acts.act_types import LinguisticActType


def test_abstention_mapping():
    assert (
        map_act_to_strategy(LinguisticActType.ABSTENTION)
        == ResponseStrategyType.ABSTENTION
    )


def test_confirmation_mapping():
    assert (
        map_act_to_strategy(LinguisticActType.REQUEST_CONFIRMATION)
        == ResponseStrategyType.CONFIRMATION
    )


def test_decision_mapping():
    assert (
        map_act_to_strategy(LinguisticActType.DECISION) == ResponseStrategyType.ACTION
    )


def test_default_mapping_information():
    assert (
        map_act_to_strategy(LinguisticActType.INFORMATION)
        == ResponseStrategyType.INFORMATIONAL
    )
