# tests/contracts/test_result_serialization_contract.py

"""The serialized consumer contract of the public result (A15-BETA-01).

The a15 audit showed the beta manifest froze the Python structure of
CognitiveResultView but not the schema of its to_dict(): a renamed JSON
key, a removed field or a changed type would not break any gate, while
that serialization is precisely what integrators consume. This suite
validates real results of the three risk bands, plus the no-decision
view, against the versioned JSON Schema shipped inside the package.
The schema file itself is frozen by fingerprint in the beta manifest.
"""

import jsonschema
import pytest

from arvis import ArvisEngine, DecisionStatus
from arvis.api.contracts.result_schema import (
    RESULT_SCHEMA_VERSION,
    load_result_schema,
)
from arvis.api.views.cognitive_result_view import CognitiveResultView

_SCHEMA = load_result_schema()
_VALIDATOR = jsonschema.Draft202012Validator(_SCHEMA)


@pytest.mark.parametrize(
    ("risk", "expected"),
    [
        (0.10, DecisionStatus.ALLOWED),
        (0.50, DecisionStatus.REQUIRES_CONFIRMATION),
        (0.90, DecisionStatus.BLOCKED),
    ],
)
def test_real_results_conform_to_the_shipped_schema(
    risk: float, expected: DecisionStatus
) -> None:
    result = ArvisEngine().run("contract", {"risk": risk})
    payload = result.to_dict()

    _VALIDATOR.validate(payload)
    assert payload["schema_version"] == RESULT_SCHEMA_VERSION
    assert payload["decision"]["status"] == expected.value


def test_schema_is_the_shipped_contract() -> None:
    """The schema pins itself: draft 2020-12, closed at the top level,
    versioned. Its bytes are frozen by the beta manifest."""
    assert _SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert _SCHEMA["additionalProperties"] is False
    assert _SCHEMA["properties"]["schema_version"]["const"] == RESULT_SCHEMA_VERSION


def test_removing_a_stable_key_breaks_the_contract() -> None:
    """Negative proof: the exact rupture class the audit described
    (a silently dropped consumer key) is detected."""
    payload = ArvisEngine().run("contract", {"risk": 0.10}).to_dict()
    del payload["global_commitment"]
    with pytest.raises(jsonschema.ValidationError):
        _VALIDATOR.validate(payload)


def test_renaming_a_stable_key_breaks_the_contract() -> None:
    payload = ArvisEngine().run("contract", {"risk": 0.10}).to_dict()
    payload["decision_v2"] = payload.pop("decision")
    with pytest.raises(jsonschema.ValidationError):
        _VALIDATOR.validate(payload)


def test_changing_a_stable_type_breaks_the_contract() -> None:
    payload = ArvisEngine().run("contract", {"risk": 0.10}).to_dict()
    payload["decision"]["status"] = 3
    with pytest.raises(jsonschema.ValidationError):
        _VALIDATOR.validate(payload)


def test_no_decision_view_conforms() -> None:
    """The minimal no-trace view (DecisionStatus.NONE) is part of the
    same contract."""
    view = CognitiveResultView(
        decision=None,
        stability=None,
        stability_view=None,
        trace=None,
        trace_view=None,
        timeline=None,
        timeline_view=None,
        timeline_commitment=None,
        global_commitment=None,
        _ir=None,
        reflexive=None,
        execution_view=None,
        commitment_policy="degraded",
        commitment_reason=None,
        commitment_degraded=True,
    )
    payload = view.to_dict()
    _VALIDATOR.validate(payload)
    assert payload["decision"]["status"] == DecisionStatus.NONE.value
