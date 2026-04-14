# arvis/kernel_core/syscalls/syscall_handler.py

from __future__ import annotations

import inspect
from typing import Any, Optional, Protocol

from arvis.kernel_core.syscalls.artifact import ExecutionArtifact
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import SyscallFn, get_syscall


class RuntimeStateLike(Protocol):
    scheduler_state: Any

    def append_event(self, name: str, payload: dict[str, Any]) -> None:
        ...


class PipelineContextLike(Protocol):
    extra: dict[str, Any]


class SyscallHandler:
    def __init__(
        self,
        runtime_state: Optional[RuntimeStateLike],
        scheduler: Any,
        services: Optional[KernelServiceRegistry] = None,
    ) -> None:
        self.runtime_state = runtime_state
        self.scheduler = scheduler
        self.services = services or KernelServiceRegistry()
        self._local_counter: int = 0
        self._last_tick: int = -1

    def handle(self, syscall: Syscall) -> SyscallResult:
        ctx: Optional[PipelineContextLike] = syscall.args.get("ctx")
        fn: Optional[SyscallFn] = get_syscall(syscall.name)
        started_tick = self._get_tick()

        if started_tick != self._last_tick:
            self._local_counter = 0
            self._last_tick = started_tick

        self._local_counter += 1

        if fn is None:
            missing_result = SyscallResult(
                success=False,
                error=f"unknown_syscall:{syscall.name}",
            )
            self._journal(
                ctx=ctx,
                syscall=syscall,
                result=missing_result,
                started_tick=started_tick,
            )
            return missing_result

        sig = inspect.signature(fn)
        try:
            sig.bind(self, **syscall.args)
        except TypeError as exc:
            error_result = SyscallResult(
                success=False,
                error=f"invalid_syscall_args:{str(exc)}",
            )
            self._journal(
                ctx=ctx,
                syscall=syscall,
                result=error_result,
                started_tick=started_tick,
            )
            return error_result

        causal_id = self._build_syscall_id(
            syscall,
            started_tick,
            self._local_counter,
        )

        try:
            syscall_result = fn(
                self,
                **{
                    **syscall.args,
                    "causal_id": causal_id,
                },
            )
        except Exception as exc:
            error_result = SyscallResult(
                success=False,
                error=f"{type(exc).__name__}:{str(exc)}",
            )
            self._journal(
                ctx=ctx,
                syscall=syscall,
                result=error_result,
                started_tick=started_tick,
            )
            return error_result

        if not isinstance(syscall_result, SyscallResult):
            syscall_result = SyscallResult(
                success=False,
                error=f"invalid_syscall_return_type:{type(syscall_result).__name__}",
            )

        self._journal(
            ctx=ctx,
            syscall=syscall,
            result=syscall_result,
            started_tick=started_tick,
        )
        return syscall_result

    def _journal(
        self,
        ctx: Optional[PipelineContextLike],
        syscall: Syscall,
        result: SyscallResult,
        started_tick: int,
    ) -> None:
        if ctx is None:
            return

        end_tick = self._get_tick()
        elapsed_ticks = self._compute_elapsed_ticks(started_tick, end_tick)
        results = ctx.extra.setdefault("syscall_results", [])

        syscall_id = self._build_syscall_id(
            syscall,
            started_tick,
            self._local_counter,
        )

        entry: dict[str, Any] = {
            "syscall_id": syscall_id,
            "causal_id": syscall_id,
            "syscall": syscall.name,
            "success": result.success,
            "elapsed_ticks": elapsed_ticks,
            "replay_policy": self._default_replay_policy(syscall.name),
            "tick": end_tick,
            "tick_start": started_tick,
            "tick_end": end_tick,
        }

        process_id = syscall.args.get("process_id")
        tick = syscall.args.get("tick")

        if process_id is not None:
            entry["process_id"] = process_id

        if tick is not None:
            entry["tick"] = tick

        if isinstance(result.result, ExecutionArtifact):
            entry["artifact"] = result.result.to_dict()
            entry["artifact_timestamp"] = result.result.timestamp
            entry["artifact"]["causal_id"] = entry["syscall_id"]
        elif result.result is not None:
            entry["result"] = result.result

        if result.error is not None:
            entry["error"] = result.error

        if isinstance(results, list):
            results.append(entry)

        ctx.extra["last_syscall_result"] = entry

        self._append_syscall_runtime_event(entry)

    def _default_replay_policy(self, syscall_name: str) -> str:
        if syscall_name == "tool.execute":
            return "journal_only_replay"

        if syscall_name.startswith("vfs.") and syscall_name not in {
            "vfs.list",
            "vfs.tree",
            "vfs.zip.analyze",
        }:
            return "journal_only_replay"

        if syscall_name in {"vfs.list", "vfs.tree", "vfs.zip.analyze"}:
            return "recompute"

        return "unknown"

    def _get_tick(self) -> int:
        if self.runtime_state is None:
            return 0
        return int(self.runtime_state.scheduler_state.tick_count)

    def _compute_elapsed_ticks(self, started_tick: int, end_tick: int) -> float:
        return float(end_tick - started_tick)

    def _build_syscall_id(
        self,
        syscall: Syscall,
        tick: int,
        seq: int,
    ) -> str:
        process_id = syscall.args.get("process_id", "none")
        return f"syscall:{syscall.name}:{process_id}:{tick}:{seq}"

    def _append_syscall_runtime_event(self, entry: dict[str, Any]) -> None:
        if self.runtime_state is None:
            return

        event_type = "syscall_succeeded" if entry.get("success") else "syscall_failed"

        payload = {
            "process_id": entry.get("process_id", "none"),
            "syscall_id": entry["syscall_id"],
            "syscall_name": entry["syscall"],
            "tick": entry.get("tick", 0),
            "replay_policy": entry.get("replay_policy"),
            "causal_id": entry["syscall_id"],
        }

        artifact = entry.get("artifact")
        if isinstance(artifact, dict):
            payload["artifact_id"] = artifact.get("id")

        self.runtime_state.append_event(event_type, payload)