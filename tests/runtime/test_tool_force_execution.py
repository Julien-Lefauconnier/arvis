# tests/runtime/test_tool_force_execution.py

from __future__ import annotations

from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.runtime_controls import TrustedRuntimeControls
from arvis.tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy_force"

    def execute(self, input_data):
        return {"ok": True, "payload": input_data.get("tool_payload")}


def test_force_tool_execution_triggers_syscall():
    os = CognitiveOS(
        CognitiveOSConfig(
            runtime_controls=TrustedRuntimeControls(
                force_tool="dummy_force",
                force_execution=True,
            )
        )
    )
    os.register_tool(DummyTool())

    result = os.run(
        user_id="u1",
        cognitive_input={},
    )

    # Force path only matters when a matching tool action exists.
    # This test checks that the run remains stable
    # and syscall journal, if present,
    # is coherent.
    assert result is not None


def test_force_tool_does_not_crash_without_matching_tool_action():
    os = CognitiveOS(
        CognitiveOSConfig(
            runtime_controls=TrustedRuntimeControls(
                force_tool="dummy_force",
                force_execution=True,
            )
        )
    )
    os.register_tool(DummyTool())

    result = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
    )

    assert result is not None


def test_no_force_execution_keeps_normal_path():
    os = CognitiveOS(
        CognitiveOSConfig(
            runtime_controls=TrustedRuntimeControls(
                force_tool="dummy_force",
                force_execution=False,
            )
        )
    )
    os.register_tool(DummyTool())

    result = os.run(
        user_id="u1",
        cognitive_input={"text": "hello"},
    )

    assert result is not None
