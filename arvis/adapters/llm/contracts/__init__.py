# arvis/adapters/llm/contracts/__init__.py
"""
Public LLM contract types.

Canonical import path for the LLM request/response contracts. Consumers should
import from here:

    from arvis.adapters.llm.contracts import LLMRequest, LLMResponse

rather than reaching into the individual submodules, which are an internal
layout detail and may move.
"""

from .request import LLMRequest
from .response import LLMResponse

__all__ = [
    "LLMRequest",
    "LLMResponse",
]
