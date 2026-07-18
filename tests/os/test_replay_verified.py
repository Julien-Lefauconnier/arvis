# tests/os/test_replay_verified.py
"""replay_verified authenticates against an external commitment (D-6)."""

from __future__ import annotations

import pytest

from arvis.api.os import CognitiveOS


def test_replay_verified_accepts_matching_commitment():
    os = CognitiveOS()
    result = os.run("user_1", {"text": "hello"})
    replay = os.replay_verified(
        result.to_ir(),
        expected_global_commitment=result.global_commitment,
    )
    assert replay.global_commitment == result.global_commitment


def test_replay_verified_rejects_commitment_mismatch():
    os = CognitiveOS()
    result = os.run("user_1", {"text": "hello"})
    with pytest.raises(RuntimeError, match="global_commitment mismatch"):
        os.replay_verified(
            result.to_ir(),
            expected_global_commitment="deadbeef",
        )


def test_replay_verified_authenticates_through_the_recomposition_path():
    # replay_verified recomposes then authenticates; the recomposed
    # commitment must equal the external anchor for the call to return.
    os = CognitiveOS()
    result = os.run("user_1", {"text": "hello"})
    expected = result.global_commitment

    replay = os.replay_verified(
        result.to_ir(),
        expected_global_commitment=expected,
    )
    assert replay is not None
    assert replay.global_commitment == expected


def test_replay_recomposed_does_not_authenticate():
    # The recomposed view carries a commitment, but no external anchor
    # is checked: it is a rebuild, not a trust decision.
    os = CognitiveOS()
    result = os.run("user_1", {"text": "hello"})
    replay = os.replay_recomposed(result.to_ir())
    assert replay is not None
    assert replay.global_commitment is not None
