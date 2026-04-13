# tests/api/test_os_replay_verification.py

from __future__ import annotations

import pytest

from arvis.api import CognitiveOS


def test_replay_verified_matches_ir() -> None:
    os = CognitiveOS()

    original = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
    )

    ir = original.to_ir()
    assert ir is not None

    replayed = os.replay_verified(
        ir,
    )

    assert replayed.to_ir() == original.to_ir()


def test_replay_verified_raises_on_commitment_mismatch() -> None:
    os = CognitiveOS()

    original = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
    )

    ir = original.to_ir()
    assert ir is not None

    with pytest.raises(RuntimeError, match="global_commitment mismatch"):
        os.replay_verified(
            ir,
            expected_global_commitment="f" * 64,
        )


def test_replay_without_expected_commitment_remains_backward_compatible() -> None:
    os = CognitiveOS()

    original = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
    )

    ir = original.to_ir()
    assert ir is not None

    replayed = os.replay(ir)

    assert replayed is not None
    assert replayed.to_ir() is not None