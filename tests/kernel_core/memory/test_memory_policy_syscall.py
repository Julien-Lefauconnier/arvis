# tests/kernel_core/memory/test_memory_policy.py

from __future__ import annotations

import pytest

from arvis.kernel_core.memory.policy import (
    MemoryAccessRequest,
    MemoryPolicyService,
)


def test_memory_policy_allows_same_user_access() -> None:
    policy = MemoryPolicyService()

    decision = policy.evaluate(
        MemoryAccessRequest(
            actor_user_id="u1",
            owner_user_id="u1",
            namespace="default",
            action="read",
            key="k1",
        )
    )

    assert decision.allowed is True
    assert decision.reason is None


def test_memory_policy_denies_cross_user_access() -> None:
    policy = MemoryPolicyService()

    decision = policy.evaluate(
        MemoryAccessRequest(
            actor_user_id="u2",
            owner_user_id="u1",
            namespace="default",
            action="read",
            key="k1",
        )
    )

    assert decision.allowed is False
    assert decision.reason == "memory_access_denied"


def test_memory_policy_denies_blank_namespace() -> None:
    policy = MemoryPolicyService()

    decision = policy.evaluate(
        MemoryAccessRequest(
            actor_user_id="u1",
            owner_user_id="u1",
            namespace="   ",
            action="list",
        )
    )

    assert decision.allowed is False
    assert decision.reason == "memory_namespace_forbidden"


def test_memory_policy_allows_none_namespace_for_global_listing() -> None:
    policy = MemoryPolicyService()

    decision = policy.evaluate(
        MemoryAccessRequest(
            actor_user_id="u1",
            owner_user_id="u1",
            namespace=None,
            action="list",
        )
    )

    assert decision.allowed is True


def test_memory_policy_require_allowed_raises_on_denial() -> None:
    policy = MemoryPolicyService()

    with pytest.raises(PermissionError, match="memory_access_denied"):
        policy.require_allowed(
            MemoryAccessRequest(
                actor_user_id="u2",
                owner_user_id="u1",
                namespace="default",
                action="write",
                key="k1",
            )
        )


def test_memory_policy_rejects_empty_actor_user_id() -> None:
    policy = MemoryPolicyService()

    with pytest.raises(ValueError, match="actor_user_id must not be empty"):
        policy.evaluate(
            MemoryAccessRequest(
                actor_user_id="",
                owner_user_id="u1",
                namespace="default",
                action="read",
            )
        )


def test_memory_policy_rejects_empty_owner_user_id() -> None:
    policy = MemoryPolicyService()

    with pytest.raises(ValueError, match="owner_user_id must not be empty"):
        policy.evaluate(
            MemoryAccessRequest(
                actor_user_id="u1",
                owner_user_id="",
                namespace="default",
                action="read",
            )
        )