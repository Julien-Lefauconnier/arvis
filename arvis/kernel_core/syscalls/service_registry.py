# arvis/kernel_core/syscalls/service_registry.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class KernelServiceRegistry:
    """
    Registry of kernel-level services available to syscalls.

    This keeps SyscallHandler scalable by avoiding constructor growth
    as new subsystems are added.
    """

    tool_executor: Optional[Any] = None
    vfs_service: Optional[Any] = None
    zip_ingest_service: Optional[Any] = None
    memory_service: Optional[Any] = None
    memory_policy_service: Optional[Any] = None