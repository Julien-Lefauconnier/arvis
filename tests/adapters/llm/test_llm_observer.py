# tests/adapters/llm/test_llm_observer.py
"""LLMObserver: the default metadata path and provider injection.

The runtime executor instantiates ``LLMObserver()`` with no provider,
so the metadata-driven branch is the one that runs in production.
Provider injection is a host seam; a test-local stub is enough to pin
it (the shipped mock provider was deleted with the dead
``observability.providers`` package, campaign STRUCT LOT S1).
"""

from typing import Any

from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.observability.observation import LLMObservation
from arvis.adapters.llm.observability.observer import LLMObserver


def _response(metadata: dict[str, Any]) -> LLMResponse:
    return LLMResponse(content="hello world", metadata=metadata)


def test_default_path_computes_signals_from_logprobs() -> None:
    observer = LLMObserver()
    obs = observer.observe(
        _response(
            {
                "logprobs": [-0.1, -0.5, -0.2],
                "token_count": 3,
                "latency_ms": 12.5,
            }
        )
    )

    assert obs is not None
    assert obs.entropy_mean is not None
    assert obs.confidence_mean is not None
    assert obs.logprob_variance is not None
    assert obs.output_length == 3
    assert obs.latency_ms == 12.5


def test_default_path_degrades_honestly_without_logprobs() -> None:
    observer = LLMObserver()
    obs = observer.observe(_response({"token_count": "not an int"}))

    assert obs is not None
    assert obs.entropy_mean is None
    assert obs.confidence_mean is None
    assert obs.logprob_variance is None
    assert obs.output_length is None


def test_default_path_survives_empty_metadata() -> None:
    observer = LLMObserver()
    obs = observer.observe(_response({}))

    assert obs is not None
    assert obs.entropy_mean is None


def test_string_logprobs_are_not_treated_as_a_sequence() -> None:
    observer = LLMObserver()
    obs = observer.observe(_response({"logprobs": "-0.1,-0.5"}))

    assert obs is not None
    assert obs.entropy_mean is None


def test_injected_provider_takes_over() -> None:
    sentinel = LLMObservation(entropy_mean=0.42)

    class _StubProvider:
        def observe(self, response: LLMResponse) -> LLMObservation:
            return sentinel

    observer = LLMObserver(_StubProvider())
    assert observer.observe(_response({"logprobs": [-1.0]})) is sentinel
