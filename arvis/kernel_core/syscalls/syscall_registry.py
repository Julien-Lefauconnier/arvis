# arvis/kernel_core/syscalls/syscall_registry.py

from __future__ import annotations

from typing import Callable, Dict, Optional

from arvis.kernel_core.syscalls.syscall import SyscallResult



SyscallFn = Callable[..., SyscallResult]

SYSCALL_REGISTRY: Dict[str, SyscallFn] = {}



def register_syscall(name: str) -> Callable[[SyscallFn], SyscallFn]:
    def decorator(fn: SyscallFn) -> SyscallFn:
        # HARDENING: prevent silent override
        if name in SYSCALL_REGISTRY:
            raise RuntimeError(f"duplicate syscall registration: {name}")
        SYSCALL_REGISTRY[name] = fn
        return fn
    return decorator


def get_syscall(name: str) -> Optional[SyscallFn]:
    return SYSCALL_REGISTRY.get(name)

