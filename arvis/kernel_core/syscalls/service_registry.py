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
    # Campaign 7 (Lot 6): production effects require a host-attested
    # AuthenticatedPrincipal on the trusted context channel. Local/test
    # profiles keep the historical declared-user fallback.
    require_authenticated_principal: bool = False
    # Campaign 5 (D-1): resolved host context (canonical, JSON-safe) and
    # the conventional instance label extracted from it. Opaque to
    # ARVIS: the label is stamped on the journaled intent and the sink
    # copy as structural provenance (ZK-safe); the full context is
    # available to services that need host provenance. Both absent when
    # the host declares none, keeping intents byte-identical to a run
    # without a host context.
    host_context: dict[str, Any] | None = None
    instance_label: str | None = None
