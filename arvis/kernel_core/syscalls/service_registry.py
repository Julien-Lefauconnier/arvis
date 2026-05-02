# arvis/kernel_core/syscalls/service_registry.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KernelServiceRegistry:
    """
    Registry of kernel-level services available to syscalls.

    This keeps SyscallHandler scalable by avoiding constructor growth
    as new subsystems are added.
    """

    tool_executor: Any | None = None
    tool_manager: Any | None = None
    vfs_service: Any | None = None
    zip_ingest_service: Any | None = None
    memory_service: Any | None = None
    memory_policy_service: Any | None = None
    llm_adapter: Any | None = None
