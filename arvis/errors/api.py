# arvis/errors/api.py

from __future__ import annotations

from arvis.errors.base import ArvisRuntimeError, ErrorDomain
from arvis.errors.codes import ErrorCode


class ArvisAPIError(ArvisRuntimeError):
    domain = ErrorDomain.API
    default_code = ErrorCode.API_ERROR
    replay_safe = True


class CognitiveStateRequiredError(ArvisAPIError):
    default_code = ErrorCode.COGNITIVE_STATE_REQUIRED


class InvalidIRPayloadError(ArvisAPIError):
    default_code = ErrorCode.INVALID_IR_PAYLOAD
