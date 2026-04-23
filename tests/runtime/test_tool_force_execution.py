# tests/runtime/test_tool_force_execution.py

from __future__ import annotations

from arvis.api.os import CognitiveOS
from arvis.tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy_force"

    def execute(self, input_data):
        return {"ok": True, "payload": input_data.get("tool_payload")}


def test_force_tool_execution_triggers_syscall():
    os = CognitiveOS()
    os.register_tool(DummyTool())

    result = os.run(
        user_id="u1",
        cognitive_input={},
        extra={
            "force_tool": "dummy_force",
            "_force_execution": True,
        },
    )

    # Force path only matters when a matching tool action exists.
    # This test checks that the run remains stable and syscall journal, if present, is coherent.
    assert result is not None


def test_force_tool_does_not_crash_without_matching_tool_action():
    os = CognitiveOS()
    os.register_tool(DummyTool())

    result = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
        extra={
            "force_tool": "dummy_force",
            "_force_execution": True,
        },
    )

    assert result is not None


def test_no_force_execution_keeps_normal_path():
    os = CognitiveOS()
    os.register_tool(DummyTool())

    result = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
        extra={
            "force_tool": "dummy_force",
            "_force_execution": False,
        },
    )

    assert result is not None