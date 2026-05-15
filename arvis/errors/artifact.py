# arvis/errors/artifact.py

from __future__ import annotations

from arvis.errors.base import ArvisInvariantViolation
from arvis.errors.codes import ErrorCode


class ArtifactError(ArvisInvariantViolation):
    default_code = ErrorCode.ARTIFACT_ERROR


class ArtifactValidationError(ArtifactError):
    default_code = ErrorCode.ARTIFACT_VALIDATION_ERROR


class ArtifactTimestampMissingError(ArtifactValidationError):
    default_code = ErrorCode.ARTIFACT_TIMESTAMP_MISSING


class ArtifactInvalidStatusError(ArtifactValidationError):
    default_code = ErrorCode.ARTIFACT_INVALID_STATUS


class ArtifactConsistencyError(ArtifactValidationError):
    default_code = ErrorCode.ARTIFACT_CONSISTENCY_ERROR
