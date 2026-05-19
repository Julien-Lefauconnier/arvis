# tests/kernel_core/test_syscall_degraded_mode.py

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.execution.cognitive_execution_state import CognitiveExecutionState
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler


def make_ctx():
    return SimpleNamespace(extra={})


def test_unknown_syscall_fails_cleanly_without_runtime_state():
    ctx = make_ctx()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    result = handler.handle(Syscall(name="unknown.call", args={"ctx": ctx}))

    assert result.success is False
    assert result.error.code == "unknown_syscall"
    assert "syscall_results" in ctx.extra
    assert ctx.extra["syscall_results"][0]["success"] is False


def test_invalid_syscall_args_fail_cleanly():
    ctx = make_ctx()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    # tool.execute attend au moins result + ctx cohérents
    result = handler.handle(Syscall(name="tool.execute", args={"ctx": ctx}))

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "invalid_syscall_args"


def test_syscall_handler_keeps_journal_even_on_failure():
    ctx = make_ctx()
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    handler.handle(Syscall(name="unknown.one", args={"ctx": ctx}))
    handler.handle(Syscall(name="unknown.two", args={"ctx": ctx}))

    entries = ctx.extra["syscall_results"]
    assert len(entries) == 2
    assert entries[0]["syscall"] == "unknown.one"
    assert entries[1]["syscall"] == "unknown.two"


def test_syscall_handler_writes_to_execution_state_journal() -> None:
    runtime = CognitiveExecutionState()
    ctx = SimpleNamespace(
        extra={},
        execution=SimpleNamespace(execution_state=runtime),
    )

    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(),
    )

    handler.handle(Syscall(name="unknown.one", args={"ctx": ctx}))

    assert len(runtime.syscall_results) == 1
    assert runtime.syscall_results[0]["syscall"] == "unknown.one"
    assert ctx.extra["syscall_results"] is runtime.syscall_results
    assert runtime.metadata["last_syscall_result"] is runtime.syscall_results[0]
