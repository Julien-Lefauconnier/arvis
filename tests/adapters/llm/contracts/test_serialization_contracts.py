# tests/adapters/llm/contracts/test_serialization_contracts.py

import json

from arvis.adapters.llm.contracts.message import LLMMessage
from arvis.adapters.llm.contracts.request import LLMRequest


def test_request_serialization():
    req = LLMRequest(messages=[LLMMessage(role="user", content="Hello")])

    data = req.model_dump()
    json.dumps(data)  # doit passer sans erreur
