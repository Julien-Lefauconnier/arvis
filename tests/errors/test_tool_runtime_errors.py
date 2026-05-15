# tests/errors/test_tool_runtime_errors.py

from arvis.errors.tool_runtime import (
    ToolAuthorizationError,
    UnknownToolError,
)


def test_tool_authorization_error():
    error = ToolAuthorizationError("forbidden")

    payload = error.to_dict()

    assert payload["domain"] == "tool"


def test_unknown_tool_error():
    error = UnknownToolError("missing")

    payload = error.to_dict()

    assert payload["retryable"] is True
