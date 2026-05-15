# tests/errors/test_artifact_errors.py

from __future__ import annotations

from arvis.errors import (
    ArtifactConsistencyError,
    ArtifactError,
    ArtifactInvalidStatusError,
    ArtifactTimestampMissingError,
    ArtifactValidationError,
    ArvisErrorCategory,
    ArvisErrorSeverity,
    ErrorCode,
)


def test_artifact_error_defaults() -> None:
    err = ArtifactError("artifact failure")

    assert err.code == ErrorCode.ARTIFACT_ERROR
    assert err.category == ArvisErrorCategory.INVARIANT
    assert err.severity == ArvisErrorSeverity.FATAL
    assert err.replay_safe is False


def test_artifact_validation_error_defaults() -> None:
    err = ArtifactValidationError("invalid artifact")

    assert err.code == ErrorCode.ARTIFACT_VALIDATION_ERROR


def test_artifact_timestamp_missing_error() -> None:
    err = ArtifactTimestampMissingError("timestamp missing")

    assert err.code == ErrorCode.ARTIFACT_TIMESTAMP_MISSING


def test_artifact_invalid_status_error() -> None:
    err = ArtifactInvalidStatusError("invalid status")

    assert err.code == ErrorCode.ARTIFACT_INVALID_STATUS


def test_artifact_consistency_error() -> None:
    err = ArtifactConsistencyError("consistency failure")

    assert err.code == ErrorCode.ARTIFACT_CONSISTENCY_ERROR
