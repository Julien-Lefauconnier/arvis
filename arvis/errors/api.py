# arvis/errors/api.py

from __future__ import annotations

from arvis.errors.base import ArvisRuntimeError


class ArvisAPIError(ArvisRuntimeError):
    default_code = "API_ERROR"
    replay_safe = True


class CognitiveStateRequiredError(ArvisAPIError):
    default_code = "COGNITIVE_STATE_REQUIRED"


class InvalidIRPayloadError(ArvisAPIError):
    default_code = "INVALID_IR_PAYLOAD"
