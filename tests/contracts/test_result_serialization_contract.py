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


def test_real_no_trace_run_conforms() -> None:
    """The audited defect (a16, blocker 1): the public no-trace path
    used to emit commitment_policy=None, rejected by the shipped
    schema. The real runtime, not a synthetic DTO, must conform."""
    from arvis import CognitiveOS, CognitiveOSConfig

    payload = (
        CognitiveOS(CognitiveOSConfig(enable_trace=False))
        .run("contract", "hello")
        .to_dict()
    )
    _VALIDATOR.validate(payload)
    assert payload["commitment_policy"] == "degraded"
    assert payload["commitment_reason"] == "trace_disabled"
    assert payload["commitment_degraded"] is True
    assert payload["decision"]["status"] in {s.value for s in DecisionStatus}


def test_no_trace_optional_policy_conforms() -> None:
    from arvis import AuditCommitmentPolicy, CognitiveOS, CognitiveOSConfig

    payload = (
        CognitiveOS(
            CognitiveOSConfig(
                enable_trace=False,
                audit_commitment_policy=AuditCommitmentPolicy.OPTIONAL,
            )
        )
        .run("contract", "hello")
        .to_dict()
    )
    _VALIDATOR.validate(payload)
    assert payload["commitment_policy"] == "optional"
    assert payload["commitment_degraded"] is False


def test_out_of_contract_view_cannot_be_built() -> None:
    """Contract invariants live in the constructor (a17): the class of
    defect where an API-producible object escapes the schema is closed
    structurally, not merely tested."""
    with pytest.raises(ValueError, match="commitment_policy"):
        CognitiveResultView(
            decision=None,
            stability=None,
            stability_view=None,
            trace=None,
            commitment_policy="not-a-policy",
        )


def test_every_public_result_path_conforms() -> None:
    """Property (a16 audit, 6.4): every CognitiveResultView produced by
    a public API validates the shipped schema: run, run_as, ask, and
    both replay paths."""
    from arvis import ArvisEngine, CognitiveOS
    from arvis.kernel_core.access.models import AuthenticatedPrincipal

    payloads = []

    os_ = CognitiveOS()
    view = os_.run("contract", {"risk": 0.10})
    payloads.append(view.to_dict())

    principal = AuthenticatedPrincipal(
        user_id="contract",
        organization_id="org-1",
        authentication_source="password",
        authentication_strength="mfa",
        session_id_hash="sha256:session",
    )
    payloads.append(CognitiveOS().run_as(principal, "hello").to_dict())

    payloads.append(ArvisEngine().ask("hello").to_dict())

    ir = view.to_ir()
    assert ir is not None
    replay_os = CognitiveOS()
    payloads.append(replay_os.replay_recomposed(ir).to_dict())
    payloads.append(
        replay_os.replay_verified(
            ir, expected_global_commitment=view.global_commitment
        ).to_dict()
    )

    for payload in payloads:
        _VALIDATOR.validate(payload)
