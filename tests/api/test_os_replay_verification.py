# tests/api/test_os_replay_verification.py
"""Authenticated replay contract (campaign 5, D-6).

replay_verified authenticates an IR against an EXTERNAL commitment; the
expected value is mandatory. replay_recomposed rebuilds an IR without
authenticating it. There is no unauthenticated replay_verified path.
"""

from __future__ import annotations

import pytest

from arvis.api import CognitiveOS


def test_replay_verified_matches_ir_when_authenticated() -> None:
    os = CognitiveOS()
    original = os.run(user_id="u1", cognitive_input={"text": "hello"})
    ir = original.to_ir()
    assert ir is not None

    replayed = os.replay_verified(
        ir,
        expected_global_commitment=original.global_commitment,
    )
    assert replayed.to_ir() == original.to_ir()


def test_replay_verified_raises_on_commitment_mismatch() -> None:
    os = CognitiveOS()
    original = os.run(user_id="u1", cognitive_input={"text": "hello"})
    ir = original.to_ir()
    assert ir is not None

    with pytest.raises(RuntimeError, match="global_commitment mismatch"):
        os.replay_verified(ir, expected_global_commitment="f" * 64)


def test_replay_verified_requires_an_expected_commitment() -> None:
    # D-6: the expected commitment is mandatory. Calling without it is a
    # TypeError (no default), not a silent unauthenticated pass.
    os = CognitiveOS()
    original = os.run(user_id="u1", cognitive_input={"text": "hello"})
    ir = original.to_ir()

    with pytest.raises(TypeError):
        os.replay_verified(ir)  # type: ignore[call-arg]


def test_replay_recomposed_rebuilds_without_authentication() -> None:
    # Recomposition without an external anchor: valid, and explicitly
    # not a trust decision.
    os = CognitiveOS()
    original = os.run(user_id="u1", cognitive_input={"text": "hello"})
    ir = original.to_ir()
    assert ir is not None

    replayed = os.replay_recomposed(ir)
    assert replayed is not None
    assert replayed.to_ir() is not None


def test_a7_replay_method_is_removed() -> None:
    # The unauthenticated a7 replay() entry point no longer exists.
    os = CognitiveOS()
    assert not hasattr(os, "replay")
