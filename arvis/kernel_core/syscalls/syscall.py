# arvis/kernel_core/syscalls/syscall.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from arvis.kernel_core.syscalls.errors import SyscallError


@dataclass(frozen=True)
class Syscall:
    name: str
    args: Mapping[str, Any]


@dataclass(frozen=True)
class SyscallResult:
    success: bool
    result: Any | None = None
    error: str | None = None

    # Production-grade structured error.
    error_detail: SyscallError | None = None

    @staticmethod
    def failure(error: SyscallError) -> SyscallResult:
        return SyscallResult(
            success=False,
            error=error.to_legacy_string(),
            error_detail=error,
        )
