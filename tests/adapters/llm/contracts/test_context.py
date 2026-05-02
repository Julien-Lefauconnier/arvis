# tests/adapters/llm/contracts/test_context.py

import pytest
from pydantic import ValidationError

from arvis.adapters.llm.contracts.context import ARVISContext


def test_valid_context():
    ctx = ARVISContext(
        risk_score=0.5,
        uncertainty_score=0.3,
        stability_score=0.8,
        confidence_score=0.9,
    )
    assert ctx.risk_score == 0.5


def test_bounds():
    with pytest.raises(ValidationError):
        ARVISContext(
            risk_score=1.5,
            uncertainty_score=0.3,
            stability_score=0.8,
            confidence_score=0.9,
        )


def test_default_lists():
    ctx = ARVISContext(
        risk_score=0.1,
        uncertainty_score=0.1,
        stability_score=0.9,
        confidence_score=0.9,
    )
    assert ctx.constraints == []
    assert ctx.objectives == []


def test_immutable():
    ctx = ARVISContext(
        risk_score=0.1,
        uncertainty_score=0.1,
        stability_score=0.9,
        confidence_score=0.9,
    )
    with pytest.raises(ValidationError):
        ctx.risk_score = 0.5
