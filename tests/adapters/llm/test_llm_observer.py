# tests/adapters/llm/test_llm_observer.py

from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.observability.observer import LLMObserver
from arvis.adapters.llm.observability.providers.mock import MockObservationProvider


class DummyResponse:
    def __init__(self, content: str):
        self.content = content
        self.metadata = {}


def test_llm_observer_basic():
    observer = LLMObserver(MockObservationProvider())

    response = DummyResponse("hello world")
    obs = observer.observe(response)

    assert obs.entropy_mean is not None
    assert obs is not None


def test_llm_observer_extracts_metrics():
    response = LLMResponse(
        content="ok",
        metadata={
            "logprobs": [-1.0, -0.5, -0.2],
            "token_count": 10,
            "latency_ms": 50,
        },
    )

    obs = LLMObserver().observe(response)

    assert obs is not None
    data = obs.to_dict()

    assert "entropy_mean" in data
    assert "confidence_mean" in data
    assert "logprob_variance" in data
