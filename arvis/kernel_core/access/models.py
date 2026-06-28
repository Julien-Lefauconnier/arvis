# arvis/kernel_core/access/models.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.kernel_core.syscalls.syscall_registry import SyscallEffect


@dataclass(slots=True, frozen=True)
class Principal:
    """Identity on whose behalf a syscall is executed.

    A bare principal (``user_id`` only, no organization, no grants) denotes the
    resource owner. This reproduces the pre-authorization behaviour, where
    access was scoped solely by ``user_id``.
    """

    user_id: str
    organization_id: str | None = None
    grants: frozenset[str] = frozenset()


@dataclass(slots=True, frozen=True)
class AccessContext:
    """The (principal, effect, resource) triple evaluated by a policy."""

    principal: Principal
    effect: SyscallEffect
    resource_owner_id: str
    resource_organization_id: str | None = None
    resource_id: str | None = None
    syscall_name: str | None = None
