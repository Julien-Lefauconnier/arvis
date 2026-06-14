# arvis/kernel_core/syscalls/syscall_registry.py

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from arvis.errors.kernel_runtime import (
    DuplicateSyscallRegistrationError,
)
from arvis.kernel_core.syscalls.syscall import SyscallResult

SyscallFn = Callable[..., SyscallResult]


class SyscallEffect(StrEnum):
    """Governance-relevant, structural effect class of a syscall.

    READ:   no state mutation and no external side-effect (idempotent).
    EFFECT: mutates governed state and/or triggers an external effect.

    This is a STRUCTURAL property declared at registration time. It is
    NOT the runtime governance verdict (ALLOW / REQUIRE_CONFIRMATION /
    ABSTAIN), which is decided per-turn by the cognitive gate.
    """

    READ = "read"
    EFFECT = "effect"


@dataclass(frozen=True)
class SyscallDescriptor:
    """Self-describing entry for a registered syscall.

    The registry is the single machine-truth of what arvis can do. Each
    descriptor pairs the capability (name + fn) with its declared,
    structural governance metadata, so the self-description layer can
    derive capabilities from the living registry instead of restating
    them in maintained-by-hand prose.
    """

    name: str
    fn: SyscallFn
    effect: SyscallEffect
    triggers_external: bool = False
    summary: str = ""


SYSCALL_REGISTRY: dict[str, SyscallFn] = {}
SYSCALL_DESCRIPTORS: dict[str, SyscallDescriptor] = {}

# Syscalls that only read state (idempotent, no side-effect). Used as the
# bootstrap default when a registration does not declare its effect. The
# authoritative source remains the per-syscall declaration at
# registration; this set only keeps coverage complete before annotation.
_DEFAULT_READ_SYSCALLS: frozenset[str] = frozenset(
    {
        "vfs.list",
        "vfs.get",
        "vfs.tree",
        "vfs.zip.analyze",
        "vfs.zip.plan",
        "memory.get",
        "memory.list",
        "memory.snapshot",
    }
)

# Prefixes whose effect leaves the sovereign boundary (non-deterministic /
# external). Bootstrap default only; overridable at registration.
_DEFAULT_EXTERNAL_PREFIXES: tuple[str, ...] = ("llm.", "tool.")


def _default_effect(name: str) -> SyscallEffect:
    if name in _DEFAULT_READ_SYSCALLS:
        return SyscallEffect.READ
    return SyscallEffect.EFFECT


def _default_triggers_external(name: str) -> bool:
    return name.startswith(_DEFAULT_EXTERNAL_PREFIXES)


def register_syscall(
    name: str,
    *,
    effect: SyscallEffect | None = None,
    triggers_external: bool | None = None,
    summary: str = "",
) -> Callable[[SyscallFn], SyscallFn]:
    def decorator(fn: SyscallFn) -> SyscallFn:
        # HARDENING: prevent silent override
        if name in SYSCALL_REGISTRY:
            raise DuplicateSyscallRegistrationError(
                f"duplicate syscall registration: {name}",
                details={
                    "syscall": name,
                },
            )

        resolved_effect = effect if effect is not None else _default_effect(name)
        resolved_external = (
            triggers_external
            if triggers_external is not None
            else _default_triggers_external(name)
        )

        SYSCALL_REGISTRY[name] = fn
        SYSCALL_DESCRIPTORS[name] = SyscallDescriptor(
            name=name,
            fn=fn,
            effect=resolved_effect,
            triggers_external=resolved_external,
            summary=summary,
        )
        return fn

    return decorator


def get_syscall(name: str) -> SyscallFn | None:
    return SYSCALL_REGISTRY.get(name)


def get_descriptor(name: str) -> SyscallDescriptor | None:
    return SYSCALL_DESCRIPTORS.get(name)


def all_descriptors() -> list[SyscallDescriptor]:
    return sorted(SYSCALL_DESCRIPTORS.values(), key=lambda d: d.name)
