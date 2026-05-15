# tests/errors/test_replay_errors.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ErrorDomain,
)
from arvis.errors.replay import (
    ReplayCognitiveStateMissing,
    ReplayGlobalCommitmentMismatch,
    ReplayGlobalCommitmentMissing,
    ReplayVerificationError,
)


def test_replay_verification_error():
    error = ReplayVerificationError("verification")

    assert error.category == ArvisErrorCategory.REPLAY
    assert error.domain == ErrorDomain.REPLAY
    assert error.severity == ArvisErrorSeverity.ERROR
    assert error.replay_safe is True


def test_replay_global_commitment_missing():
    error = ReplayGlobalCommitmentMissing("missing")

    assert error.default_code == ("replay_global_commitment_missing")


def test_replay_global_commitment_mismatch():
    error = ReplayGlobalCommitmentMismatch("mismatch")

    assert error.default_code == ("replay_global_commitment_mismatch")


def test_replay_cognitive_state_missing():
    error = ReplayCognitiveStateMissing("missing state")

    assert error.default_code == ("replay_cognitive_state_missing")
