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
    llm_adapter: Any | None = None
    authorization_service: Any | None = None
    # F-008-a5: host sink for durable audit intents. Called
    # synchronously BEFORE any effect syscall runs; a failing sink
    # refuses the syscall (fail-closed): an intent that cannot be made
    # durable must not be followed by its effect.
    audit_intent_sink: Any | None = None
    # D4-e (P1-a6): production posture. When set, an effect syscall
    # with no durable sink configured is refused at the point of use
    # (reason durable_sink_required): effectful production requires
    # durability, production without effects stays valid without a
    # sink.
    require_durable_intent_sink: bool = False
