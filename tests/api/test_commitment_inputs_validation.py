# tests/api/test_commitment_inputs_validation.py
"""Strict commitment_inputs validation (P0-2-a6).

An incomplete or forged proof block must never compose into a formally
valid commitment: validation requires exactly the four component keys
with canonical sha256 hex values, fail-closed. Under REQUIRED an
invalid block refuses the result; under DEGRADED it surfaces as an
absent commitment with the dedicated reason.
"""

import pytest

from arvis import CognitiveOS, CognitiveOSConfig
from arvis.api.commitment import (
    CommitmentInputs,
    CommitmentInputsValidationError,
    compose_global_commitment,
    validate_commitment_inputs,
)
from arvis.errors.base import ArvisSecurityError

_H = "a" * 64


def _valid_block() -> dict:
    return {
        "registry_fingerprint": _H,
        "config_fingerprint": _H,
        "policies_fingerprint": _H,
        "syscall_journal_sha256": _H,
    }


# ---------------------------------------------------------------
# Unit validation
# ---------------------------------------------------------------


def test_valid_block_is_accepted_and_typed():
    validated = validate_commitment_inputs(_valid_block())
    assert isinstance(validated, CommitmentInputs)
    assert validated.to_dict() == _valid_block()


def test_empty_block_is_rejected():
    with pytest.raises(CommitmentInputsValidationError, match="mismatch"):
        validate_commitment_inputs({})


def test_missing_key_is_rejected():
    block = _valid_block()
    del block["syscall_journal_sha256"]
    with pytest.raises(CommitmentInputsValidationError, match="missing"):
        validate_commitment_inputs(block)


def test_extra_key_is_rejected():
    block = _valid_block()
    block["extra_component"] = _H
    with pytest.raises(CommitmentInputsValidationError, match="extra"):
        validate_commitment_inputs(block)


@pytest.mark.parametrize(
    "bad",
    [
        "zz",  # not hex, wrong length
        "A" * 64,  # uppercase is not canonical
        "a" * 63,  # wrong length
        42,  # not a string
        None,
        ["a" * 64],
    ],
)
def test_malformed_sha256_values_are_rejected(bad):
    block = _valid_block()
    block["config_fingerprint"] = bad
    with pytest.raises(CommitmentInputsValidationError, match="sha256"):
        validate_commitment_inputs(block)


def test_non_mapping_block_is_rejected():
    with pytest.raises(CommitmentInputsValidationError, match="mapping"):
        validate_commitment_inputs("not a dict")


def test_compose_refuses_invalid_inputs():
    # P0-2-a6: `.get(key)` permissiveness is gone; composition over an
    # incomplete block raises instead of hashing None components.
    with pytest.raises(CommitmentInputsValidationError):
        compose_global_commitment(
            ir_hash="i", timeline_commitment="t", commitment_inputs={}
        )


# ---------------------------------------------------------------
# Adversarial replay (production, REQUIRED)
# ---------------------------------------------------------------


def _production_run():
    os_ = CognitiveOS(config=CognitiveOSConfig.production())
    return os_, os_.run("u1", {"risk": 0.1})


@pytest.mark.parametrize(
    "forge",
    [
        lambda block: {},
        lambda block: {k: v for k, v in block.items() if k != "config_fingerprint"},
        lambda block: {**block, "extra_key": _H},
        lambda block: {**block, "registry_fingerprint": "zz"},
        lambda block: {**block, "syscall_journal_sha256": 42},
        lambda block: "not a dict",
    ],
)
def test_forged_commitment_inputs_are_rejected_in_production(forge):
    os_, run = _production_run()
    ir = run.to_ir()
    ir["commitment_inputs"] = forge(ir["commitment_inputs"])
    with pytest.raises(ArvisSecurityError):
        os_.replay_recomposed(ir)


def test_legitimate_replay_still_verifies_in_production():
    os_, run = _production_run()
    replayed = os_.replay_verified(
        run.to_ir(), expected_global_commitment=run.global_commitment
    )
    assert replayed.global_commitment == run.global_commitment


def test_degraded_profile_flags_invalid_inputs_with_dedicated_reason():
    os_ = CognitiveOS()  # DEGRADED default
    run = os_.run("u1", {"risk": 0.1})
    ir = run.to_ir()
    ir["commitment_inputs"] = {}
    replayed = os_.replay_recomposed(ir)
    data = replayed.to_dict()
    assert replayed.global_commitment is None
    assert data["commitment_degraded"] is True
    assert data["commitment_reason"] == "commitment_inputs_invalid"


def test_exported_block_is_the_canonical_validated_form():
    _, run = _production_run()
    block = run.to_ir()["commitment_inputs"]
    validated = validate_commitment_inputs(block)
    assert validated.to_dict() == block
