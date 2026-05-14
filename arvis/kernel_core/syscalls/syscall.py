# arvis/kernel_core/syscalls/syscall.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from arvis.errors.base import ArvisError


@dataclass(frozen=True)
class Syscall:
    name: str
    args: Mapping[str, Any]


@dataclass(frozen=True)
class SyscallResult:
    success: bool
    result: Any | None = None
    error: ArvisError | None = None

    @staticmethod
    def failure(error: ArvisError) -> SyscallResult:
        return SyscallResult(
            success=False,
            error=error,
        )
