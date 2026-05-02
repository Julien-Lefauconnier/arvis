# tests/kernel/pipeline/test_runtime_bindings.py

from __future__ import annotations

from arvis.kernel.pipeline.runtime_bindings import PipelineRuntimeBindings
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult


class DummyHandler:
    def handle(self, syscall: Syscall) -> SyscallResult:
        return SyscallResult(success=True)


def test_pipeline_runtime_bindings_are_immutable() -> None:
    bindings = PipelineRuntimeBindings(
        syscall_handler=DummyHandler(),
        process_id="proc-1",
    )

    assert bindings.process_id == "proc-1"
