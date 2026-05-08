# tests/adapters/llm/test_llm_risk_mapper.py

import pytest

from arvis.adapters.llm.observability.evaluation import (
    LLMEvaluation,
)
from arvis.adapters.llm.observability.observation import (
    LLMObservation,
)
from arvis.adapters.llm.observability.risk_mapper import (
    LLMRiskSignalMapper,
)


def test_llm_risk_mapper_empty_inputs():
    mapper = LLMRiskSignalMapper()

    signal = mapper.build(
        observation=None,
        evaluation=None,
    )

    assert signal.risk_pressure == 0.0


def test_llm_risk_mapper_observation_only():
    mapper = LLMRiskSignalMapper()

    observation = LLMObservation(
        entropy_mean=0.4,
        confidence_mean=0.7,
        logprob_variance=0.5,
    )

    signal = mapper.build(
        observation=observation,
        evaluation=None,
    )

    assert signal.entropy_pressure == pytest.approx(0.4)
    assert signal.confidence_risk == pytest.approx(0.3)
    assert signal.variance_pressure == pytest.approx(0.5)
    assert signal.risk_pressure == pytest.approx(0.5)


def test_llm_risk_mapper_evaluation_only():
    mapper = LLMRiskSignalMapper()

    evaluation = LLMEvaluation(
        risk=0.8,
        uncertainty=0.6,
    )

    signal = mapper.build(
        observation=None,
        evaluation=evaluation,
    )

    assert signal.evaluation_risk == 0.8
    assert signal.uncertainty_pressure == 0.6
    assert signal.risk_pressure == 0.8


def test_llm_risk_mapper_combined_sources():
    mapper = LLMRiskSignalMapper()

    observation = LLMObservation(
        entropy_mean=0.3,
        confidence_mean=0.4,
        logprob_variance=0.2,
    )

    evaluation = LLMEvaluation(
        risk=0.75,
        uncertainty=0.5,
    )

    signal = mapper.build(
        observation=observation,
        evaluation=evaluation,
    )

    assert signal.entropy_pressure == 0.3
    assert signal.confidence_risk == 0.6
    assert signal.variance_pressure == 0.2
    assert signal.evaluation_risk == 0.75
    assert signal.uncertainty_pressure == 0.5

    assert signal.risk_pressure == 0.75
