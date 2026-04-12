# arvis/runtime/process_hooks.py

from __future__ import annotations
from typing import Protocol, Any, Optional

from arvis.kernel_core.process.process import CognitiveProcess

class ProcessHook(Protocol):
    def on_process_enqueued(self, process: CognitiveProcess) -> None: ...
    def on_process_selected(self, process: CognitiveProcess, score: Optional[float]) -> None: ...
    def on_process_completed(self, process: CognitiveProcess, result: Any) -> None: ...
    def on_process_aborted(self, process: CognitiveProcess, error: str) -> None: ...
    def on_process_blocked(self, process: CognitiveProcess, reason: str) -> None: ...
    def on_process_suspended(self, process: CognitiveProcess, reason: str) -> None: ...
    def on_process_waiting_confirmation(self, process: CognitiveProcess) -> None: ...

class ProcessHookManager:

    def __init__(self, runtime_state: Optional[Any] = None) -> None:
        self._hooks: list[ProcessHook] = []
        self.runtime_state = runtime_state


    def register(self, hook: ProcessHook) -> None:
        self._hooks.append(hook)

    def on_enqueued(self, process: CognitiveProcess) -> None:
        for h in self._hooks:
            try:
                h.on_process_enqueued(process)
            except Exception as e:
                self._emit_error("on_process_enqueued", process, e)
            

    def on_selected(self, process: CognitiveProcess, score: Optional[float]) -> None:
        for h in self._hooks:
            try:
                h.on_process_selected(process, score)
            except Exception as e:
                self._emit_error("on_process_selected", process, e)


    def on_completed(self, process: CognitiveProcess, result: Any) -> None:
        for h in self._hooks:
            try:
                h.on_process_completed(process, result)
            except Exception as e:
                self._emit_error("on_process_completed", process, e)

    def on_aborted(self, process: CognitiveProcess, error: str) -> None:
        for h in self._hooks:
            try:
                h.on_process_aborted(process, error)
            except Exception as e:
                self._emit_error("on_process_aborted", process, e)

    def on_blocked(self, process: CognitiveProcess, reason: str) -> None:
        for h in self._hooks:
            try:
                h.on_process_blocked(process, reason)
            except Exception as e:
                self._emit_error("on_process_blocked", process, e)

    def on_suspended(self, process: CognitiveProcess, reason: str) -> None:
        for h in self._hooks:
            try:
                h.on_process_suspended(process, reason)
            except Exception as e:
                self._emit_error("on_process_suspended", process, e)

    def on_waiting_confirmation(self, process: CognitiveProcess) -> None:
        for h in self._hooks:
            try:
                h.on_process_waiting_confirmation(process)
            except Exception as e:
                self._emit_error("on_process_waiting_confirmation", process, e)

    # -----------------------------------------
    # INTERNAL
    # -----------------------------------------
    def _emit_error(self, hook_name: str, process: CognitiveProcess, exc: Exception) -> None:
        if self.runtime_state:
            self.runtime_state.append_event(
                "hook_error",
                {
                    "process_id": process.process_id.value,
                    "hook": hook_name,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )