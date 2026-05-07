# tests/adapters/llm/test_llm_evaluator.py

from arvis.adapters.llm.observability.observation import LLMObservation
from arvis.adapters.llm.runtime.evaluator import LLMResponseEvaluator


def test_evaluator_accept():
    evaluator = LLMResponseEvaluator()

    obs = LLMObservation(
        entropy_mean=0.5,
        confidence_mean=0.8,
        logprob_variance=0.05,
    )

    decision = evaluator.evaluate(obs)

    assert decision.accept is True
    assert decision.retry is False
    assert decision.fallback is False


def test_evaluator_retry_high_entropy():
    evaluator = LLMResponseEvaluator()

    obs = LLMObservation(
        entropy_mean=2.0,
        confidence_mean=0.5,
        logprob_variance=0.1,
    )

    decision = evaluator.evaluate(obs)

    assert decision.retry is True
    assert decision.require_confirmation is True


def test_evaluator_retry_high_variance():
    evaluator = LLMResponseEvaluator()

    obs = LLMObservation(
        entropy_mean=0.5,
        confidence_mean=0.5,
        logprob_variance=0.3,
    )

    decision = evaluator.evaluate(obs)

    assert decision.retry is True


def test_evaluator_fallback_low_confidence():
    evaluator = LLMResponseEvaluator()

    obs = LLMObservation(
        entropy_mean=0.5,
        confidence_mean=0.1,
        logprob_variance=0.05,
    )

    decision = evaluator.evaluate(obs)

    assert decision.fallback is True
    assert decision.require_confirmation is True


def test_evaluator_none_observation():
    evaluator = LLMResponseEvaluator()

    decision = evaluator.evaluate(None)

    assert decision.accept is True
