# tests/os/test_replay_verified.py

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


def test_replay_verified_delegates_to_replay(monkeypatch):
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    expected = result.global_commitment

    called = {"ok": False}
    original_replay = os.replay

    def wrapped_replay(*args, **kwargs):
        called["ok"] = True
        return original_replay(*args, **kwargs)

    monkeypatch.setattr(os, "replay", wrapped_replay)

    replay = os.replay_verified(
        result.to_ir(),
        expected_global_commitment=expected,
    )

    assert called["ok"] is True
    assert replay is not None
    assert replay.global_commitment == expected
