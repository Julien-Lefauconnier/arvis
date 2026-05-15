# arvis/errors/tool_runtime.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisExternalError,
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.errors.codes import ErrorCode


class ToolExecutionError(ArvisRuntimeError):
    domain = ErrorDomain.TOOL
    default_code = ErrorCode.TOOL_EXECUTION_ERROR
    replay_safe = False


class ToolAuthorizationError(ToolExecutionError):
    default_code = ErrorCode.TOOL_AUTHORIZATION_ERROR
    replay_safe = True


class UnknownToolError(ArvisExternalError):
    domain = ErrorDomain.TOOL
    default_code = ErrorCode.TOOL_UNKNOWN
    replay_safe = False
