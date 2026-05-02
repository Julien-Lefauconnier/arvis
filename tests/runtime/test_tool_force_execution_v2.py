# tests/runtime/test_tool_force_execution_v2.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.api.os import CognitiveOS
from arvis.tools.base import BaseTool


class DummyTool(BaseTool):
    name = "dummy_force_v3"

    def execute(self, input_data):
        return {"ok": True, "tool_payload": input_data.get("tool_payload")}


class DummySpec:
    def __init__(self, name):
        self.name = name


def test_force_tool_executes_when_matching_action_exists():
    os = CognitiveOS()
    os.register_tool(DummyTool())
    ctx = os._build_context(
        "u1",
        {},
        extra={
            "force_tool": "dummy_force_v3",
            "_force_execution": True,
        },
    )

    # 🔑 inject a fake decision to simulate pipeline output
    fake_action = SimpleNamespace(
        tool="dummy_force_v3",
        tool_payload={"x": 42},
        allowed=False,
        requires_confirmation=True,
        can_execute=False,
    )

    fake_result = SimpleNamespace(
        action_decision=fake_action,
    )

    os.runtime._execute_tool_if_needed(
        ctx=ctx,
        process=SimpleNamespace(process_id=SimpleNamespace(value="p1")),
        result=fake_result,
    )

    syscall_results = ctx.extra.get("syscall_results", [])
    assert len(syscall_results) == 1
    assert syscall_results[0]["success"] is True


def test_force_tool_non_matching_name_does_not_change_manual_syscall_behavior():
    os = CognitiveOS()
    os.register_tool(DummyTool())

    fake_action = SimpleNamespace(
        tool="another_tool",
        tool_payload={"x": 1},
        spec=DummySpec("another_tool"),
        allowed=True,
        requires_confirmation=False,
        can_execute=True,
    )

    fake_result = SimpleNamespace(
        action_decision=fake_action,
        can_execute=True,
        requires_confirmation=False,
    )

    syscall_result = os.runtime.syscall_handler.handle(
        __import__("arvis.kernel_core.syscalls.syscall", fromlist=["Syscall"]).Syscall(
            name="tool.execute",
            args={
                "result": fake_result,
                "ctx": os._build_context("u1", {}, extra={}),
                "process_id": "proc::u1::manual",
            },
        )
    )

    assert syscall_result.success is False


def test_force_tool_unknown_tool_fails_cleanly():
    os = CognitiveOS()

    fake_action = SimpleNamespace(
        tool="missing_tool",
        tool_payload={},
        spec=DummySpec("missing_tool"),
        allowed=True,
        requires_confirmation=False,
        can_execute=True,
    )

    fake_result = SimpleNamespace(
        action_decision=fake_action,
        can_execute=True,
        requires_confirmation=False,
    )

    syscall_result = os.runtime.syscall_handler.handle(
        __import__("arvis.kernel_core.syscalls.syscall", fromlist=["Syscall"]).Syscall(
            name="tool.execute",
            args={
                "result": fake_result,
                "ctx": os._build_context("u1", {}, extra={}),
                "process_id": "proc::u1::manual",
            },
        )
    )

    assert syscall_result.success is False
    assert syscall_result.error is not None
