# tests/adapters/llm/contracts/test_request_v2.py

import pytest
from pydantic import ValidationError

from arvis.adapters.llm.contracts.message import LLMMessage
from arvis.adapters.llm.contracts.request import LLMRequest


def test_basic_request():
    req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])
    assert len(req.messages) == 1


def test_with_options_and_context():
    req = LLMRequest(
        messages=[LLMMessage(role="user", content="Hello")],
    )
    assert req.options is not None


def test_empty_messages_invalid():
    with pytest.raises(ValidationError):
        LLMRequest(messages=[])


def test_tags_default():
    req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])
    assert req.tags == []


def test_immutable():
    req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])
    with pytest.raises(ValidationError):
        req.tags = ["changed"]
