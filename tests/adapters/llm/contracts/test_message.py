# tests/adapters/llm/contracts/test_message.py

import pytest
from pydantic import ValidationError

from arvis.adapters.llm.contracts.message import LLMMessage


def test_valid_message():
    msg = LLMMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"


def test_invalid_role():
    with pytest.raises(ValidationError):
        LLMMessage(role="invalid", content="Hello")


def test_empty_content():
    with pytest.raises(ValidationError):
        LLMMessage(role="user", content="")


def test_optional_fields():
    msg = LLMMessage(
        role="assistant",
        content="Hi",
        name="assistant_1",
        tool_call_id="tool_123",
    )
    assert msg.name == "assistant_1"
    assert msg.tool_call_id == "tool_123"


def test_immutable():
    msg = LLMMessage(role="user", content="Hello")
    with pytest.raises(ValidationError):
        msg.content = "Changed"
