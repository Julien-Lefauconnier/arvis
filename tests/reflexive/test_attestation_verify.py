# tests/reflexive/test_attestation_verify.py

"""The reflexive attestation verifies its final public payload (A15-BETA-02).

The a15 audit probe: the published fingerprint was computed on an
intermediate state where ``attestation`` was None and ``exposed_views``
had been injected by the service, so recomputing on the final payload
gave a different fingerprint unless the consumer knew both implicit
transformations. This suite pins the inverse contract: the payload as
exposed verifies directly through the public API, and altering any
attested surface is detected fail-closed.
"""

import copy

import pytest

from arvis import CognitiveOS, verify_reflexive_attestation
from arvis.reflexive.attestation.reflexive_attestation import (
    ATTESTATION_CANON_VERSION,
    ReflexiveAttestation,
)


def _payload() -> dict:
    result = CognitiveOS().run(user_id="u1", cognitive_input="test")
    assert result.reflexive is not None
    return result.reflexive


def test_audit_probe_inverted_final_payload_verifies_directly() -> None:
    payload = _payload()
    published = payload["attestation"]["fingerprint"]
    recomputed = ReflexiveAttestation.from_rendered_payload(payload).fingerprint
    assert recomputed == published
    assert verify_reflexive_attestation(payload) is True


def test_payload_carries_every_reconstruction_parameter() -> None:
    """No input has to be fished out of the attestation itself."""
    payload = _payload()
    assert "exposed_views" in payload
    assert "mode" in payload
    assert payload["attestation"]["canon_version"] == ATTESTATION_CANON_VERSION


def test_verify_does_not_mutate_the_payload() -> None:
    payload = _payload()
    before = copy.deepcopy(payload)
    verify_reflexive_attestation(payload)
    assert payload == before


def test_altering_the_attested_state_is_detected() -> None:
    payload = _payload()
    payload["cognitive_state"]["bundle_id"] = "forged"
    assert verify_reflexive_attestation(payload) is False


def test_altering_capabilities_is_detected() -> None:
    payload = _payload()
    payload["capabilities"] = {"forged": True}
    assert verify_reflexive_attestation(payload) is False


def test_removing_an_attested_key_is_detected() -> None:
    payload = _payload()
    del payload["introspection"]
    assert verify_reflexive_attestation(payload) is False


def test_tampering_with_the_published_fingerprint_is_detected() -> None:
    payload = _payload()
    payload["attestation"]["fingerprint"] = "0" * 64
    assert verify_reflexive_attestation(payload) is False


def test_tampering_with_exposed_views_is_detected() -> None:
    payload = _payload()
    payload["exposed_views"] = ["injected_view"]
    assert verify_reflexive_attestation(payload) is False


def test_missing_or_malformed_attestation_fails_closed() -> None:
    payload = _payload()
    stripped = dict(payload)
    stripped["attestation"] = None
    assert verify_reflexive_attestation(stripped) is False
    assert verify_reflexive_attestation({}) is False
    assert verify_reflexive_attestation({"attestation": "not-a-dict"}) is False


def test_attestation_object_is_deeply_immutable() -> None:
    payload = _payload()
    attestation = ReflexiveAttestation.from_rendered_payload(payload)
    assert isinstance(attestation.exposed_views, tuple)
    assert attestation.immutability is True


def test_fingerprint_is_a_pure_function_of_the_canonical_source() -> None:
    """The documented meaning of ``deterministic``: same payload, same
    fingerprint; run-level identity across executions is not claimed."""
    payload = _payload()
    first = ReflexiveAttestation.from_rendered_payload(payload).fingerprint
    second = ReflexiveAttestation.from_rendered_payload(payload).fingerprint
    assert first == second


# ---------------------------------------------------------------------
# A17 lot 2: the ENTIRE attestation block is verified (audit a16,
# blocker 2): every metadata field, the audit's eight probes replayed.
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "forged"),
    [
        ("type", "forged_type"),
        ("scope", "forged_scope"),
        ("authority", "user"),
        ("immutability", False),
        ("deterministic", False),
        ("mode", "forged_mode"),
        ("exposed_views", ["forged_view"]),
        ("canon_version", "999.0"),
    ],
)
def test_forging_any_attestation_field_fails(field: str, forged) -> None:
    """The a16 audit probes, replayed: each one used to verify True."""
    payload = _payload()
    payload["attestation"][field] = forged
    assert verify_reflexive_attestation(payload) is False


def test_consistent_mode_rewrite_fails() -> None:
    """Canonicalization 2.0: mode is an attested member of the source,
    so rewriting it consistently in BOTH the payload root and the
    attestation block still changes the fingerprint and fails."""
    payload = _payload()
    payload["mode"] = "observation_only"
    payload["attestation"]["mode"] = "observation_only"
    assert verify_reflexive_attestation(payload) is False


def test_extra_or_missing_attestation_key_fails() -> None:
    payload = _payload()
    payload["attestation"]["injected"] = True
    assert verify_reflexive_attestation(payload) is False
    payload = _payload()
    del payload["attestation"]["authority"]
    assert verify_reflexive_attestation(payload) is False


@pytest.mark.parametrize("malformed", [None, [], "x", 42, 3.14, {"a": 1}])
def test_malformed_input_fails_closed(malformed) -> None:
    """7.4: the boundary verifier returns False for every invalid
    shape; it never raises (AttributeError included)."""
    assert verify_reflexive_attestation(malformed) is False


def test_unknown_canon_version_is_refused_before_any_computation() -> None:
    payload = _payload()
    payload["attestation"]["canon_version"] = "1.0"
    assert verify_reflexive_attestation(payload) is False


def test_non_finite_attested_value_is_refused_as_non_json() -> None:
    payload = _payload()
    payload["capabilities"]["non_finite"] = float("nan")

    with pytest.raises(ValueError, match="JSON compliant"):
        ReflexiveAttestation.from_rendered_payload(payload)
    assert verify_reflexive_attestation(payload) is False


def test_hostile_container_subclass_fails_closed() -> None:
    """b1 (audit a17, 13.3): a dict subclass raising from get() is
    absorbed by the boundary verifier, never propagated."""

    class _EvilDict(dict):
        def get(self, *args, **kwargs):
            raise RuntimeError("boom")

    assert verify_reflexive_attestation(_EvilDict()) is False
