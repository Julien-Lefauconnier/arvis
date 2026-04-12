# arvis/kernel_core/syscalls/syscall_handler.py

from __future__ import annotations

from typing import Any, Optional, Protocol

from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import get_syscall, SyscallFn


class RuntimeStateLike(Protocol):
    def append_event(self, name: str, payload: dict[str, Any]) -> None: ...


class PipelineContextLike(Protocol):
    extra: dict[str, Any]


class SyscallHandler:
    def __init__(
        self,
        runtime_state: Optional[RuntimeStateLike],
        scheduler: Any,
        tool_executor: Optional[Any] = None,
    ) -> None:
        self.runtime_state = runtime_state
        self.scheduler = scheduler
        self.tool_executor = tool_executor

    def handle(self, syscall: Syscall) -> SyscallResult:
        ctx: Optional[PipelineContextLike] = syscall.args.get("ctx")
        fn: Optional[SyscallFn] = get_syscall(syscall.name)

        if fn is None:
            missing_result = SyscallResult(
                success=False,
                error=f"unknown_syscall:{syscall.name}",
            )
            self._journal(ctx, syscall.name, missing_result)
            return missing_result

        try:
            syscall_result = fn(self, **syscall.args)
        except Exception as e:
            error_result = SyscallResult(
                success=False,
                error=f"{type(e).__name__}:{str(e)}",
            )
            self._journal(ctx, syscall.name, error_result)
            return error_result

        self._journal(ctx, syscall.name, syscall_result)
        return syscall_result
    
    def _journal(
        self,
        ctx: Optional[PipelineContextLike],
        syscall_name: str,
        result: SyscallResult,
    ) -> None:
        if ctx is None:
            return
 
        results = ctx.extra.setdefault("syscall_results", [])

        entry: dict[str, Any] = {
            "syscall": syscall_name,
            "success": result.success,
        }

        if result.result is not None:
            entry["result"] = result.result

        if result.error is not None:
            entry["error"] = result.error

        if isinstance(results, list):
            results.append(entry)
