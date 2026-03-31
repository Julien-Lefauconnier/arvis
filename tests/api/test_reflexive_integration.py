# tests/api/test_reflexive_integration.py

import pytest

from arvis.api.os import CognitiveOS


# -----------------------------------------------------
# BASIC INTEGRATION
# -----------------------------------------------------

def test_os_result_contains_reflexive_field():
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="hello"
    )

    assert hasattr(result, "reflexive")


def test_reflexive_payload_optional():
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    # Reflexive may be None depending on pipeline state
    assert result.reflexive is None or isinstance(result.reflexive, dict)


# -----------------------------------------------------
# STRUCTURE TEST (if present)
# -----------------------------------------------------

def test_reflexive_payload_structure_if_present():
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    r = result.reflexive

    if r is None:
        pytest.skip("Reflexive not available (no cognitive_state)")

    assert "mode" in r
    assert "capabilities" in r
    assert "timeline_views" in r
    assert "generated_at" in r


# -----------------------------------------------------
# ATTESTATION TEST
# -----------------------------------------------------

def test_reflexive_attestation_if_present():
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    r = result.reflexive

    if r is None:
        pytest.skip("Reflexive not available")

    assert "attestation" in r
    assert r["attestation"] is not None


# -----------------------------------------------------
# NON BREAKING CONTRACT
# -----------------------------------------------------

def test_to_dict_does_not_include_reflexive():
    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input="test"
    )

    d = result.to_dict()

    # Reflexive must NOT be exposed in public JSON
    assert "reflexive" not in d


# -----------------------------------------------------
# DETERMINISM (weak)
# -----------------------------------------------------

def test_reflexive_mode_stable():
    os = CognitiveOS()

    r1 = os.run("u1", "same input").reflexive
    r2 = os.run("u1", "same input").reflexive

    if r1 is None or r2 is None:
        pytest.skip("Reflexive not available")

    assert r1["mode"] == r2["mode"]