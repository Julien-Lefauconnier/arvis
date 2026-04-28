# tests/api/test_replay_corrupted_ir.py

from __future__ import annotations

import copy

import pytest

from arvis.api.os import CognitiveOS


def test_replay_rejects_missing_context():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    ir = copy.deepcopy(result.to_ir())

    assert ir is not None
    ir.pop("context", None)

    with pytest.raises(Exception):
        os.replay(ir)


def test_replay_rejects_missing_input():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    ir = copy.deepcopy(result.to_ir())

    assert ir is not None
    ir.pop("input", None)

    with pytest.raises(Exception):
        os.replay(ir)


def test_replay_rejects_structurally_corrupted_ir():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    ir = copy.deepcopy(result.to_ir())

    assert ir is not None
    ir["context"] = "not-a-dict"

    with pytest.raises(Exception):
        os.replay(ir)
