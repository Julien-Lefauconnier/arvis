# arvis/kernel_core/memory/policy.py

from __future__ import annotations

from dataclasses import dataclass

MemoryAction = str  # "read" | "write" | "delete" | "list"


@dataclass(frozen=True)
class MemoryAccessRequest:
    """
    Canonical memory access request evaluated by kernel policy.

    This object is intentionally small and deterministic so policy evaluation
    remains explicit, testable, and replay-safe.
    """

    actor_user_id: str
    owner_user_id: str
    namespace: str | None
    action: MemoryAction
    key: str | None = None


@dataclass(frozen=True)
class MemoryPolicyDecision:
    """
    Result of a memory policy evaluation.
    """

    allowed: bool
    reason: str | None = None


class MemoryPolicyService:
    """
    Kernel-level authorization layer for memory access.

    V1 policy goals:
    - deterministic decisions
    - explicit ownership boundary
    - namespace-aware validation
    - no implicit privilege escalation
    """

    def evaluate(self, request: MemoryAccessRequest) -> MemoryPolicyDecision:
        self._validate_request(request)

        if request.actor_user_id != request.owner_user_id:
            return MemoryPolicyDecision(
                allowed=False,
                reason="memory_access_denied",
            )

        if request.namespace is not None and not request.namespace.strip():
            return MemoryPolicyDecision(
                allowed=False,
                reason="memory_namespace_forbidden",
            )

        return MemoryPolicyDecision(
            allowed=True,
            reason=None,
        )

    def require_allowed(self, request: MemoryAccessRequest) -> None:
        decision = self.evaluate(request)
        if not decision.allowed:
            raise PermissionError(decision.reason or "memory_policy_violation")

    def _validate_request(self, request: MemoryAccessRequest) -> None:
        if not request.actor_user_id.strip():
            raise ValueError("actor_user_id must not be empty")

        if not request.owner_user_id.strip():
            raise ValueError("owner_user_id must not be empty")

        if not request.action.strip():
            raise ValueError("action must not be empty")
