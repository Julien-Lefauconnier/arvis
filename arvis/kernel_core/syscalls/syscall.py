# arvis/kernel_core/syscalls/syscall.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Syscall:
    name: str
    args: Mapping[str, Any]


@dataclass(frozen=True)
class SyscallResult:
    success: bool
    result: Any | None = None
    error: str | None = None
