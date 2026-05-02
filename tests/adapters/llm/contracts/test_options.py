# tests/adapters/llm/contracts/test_options.py

import pytest
from pydantic import ValidationError

from arvis.adapters.llm.contracts.options import LLMOptions


def test_default_options():
    opts = LLMOptions()
    assert opts.temperature == 0.7
    assert opts.max_tokens == 512


def test_valid_bounds():
    opts = LLMOptions(temperature=0.0, max_tokens=1)
    assert opts.temperature == 0.0
    assert opts.max_tokens == 1


def test_invalid_temperature_low():
    with pytest.raises(ValidationError):
        LLMOptions(temperature=-0.1)


def test_invalid_temperature_high():
    with pytest.raises(ValidationError):
        LLMOptions(temperature=2.1)


def test_invalid_max_tokens():
    with pytest.raises(ValidationError):
        LLMOptions(max_tokens=0)


def test_immutable():
    opts = LLMOptions()
    with pytest.raises(ValidationError):
        opts.temperature = 1.0
