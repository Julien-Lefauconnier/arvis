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


class ToolTimeoutError(ToolExecutionError):
    """F-014: the tool ran past its declared timeout budget and its late
    result was rejected (deadline on result acceptance, not an
    interruption; the effect may still have happened)."""

    default_code = ErrorCode.TOOL_TIMEOUT
    replay_safe = False


class ToolInputValidationError(ToolExecutionError):
    """F-020: the payload violates the tool's declared input_schema and
    never reached the tool."""

    default_code = ErrorCode.TOOL_INPUT_INVALID
    replay_safe = True


class ToolOutputValidationError(ToolExecutionError):
    """F-020: the tool response violates its declared output_schema and
    must not flow downstream as a success."""

    default_code = ErrorCode.TOOL_OUTPUT_INVALID
    replay_safe = False
