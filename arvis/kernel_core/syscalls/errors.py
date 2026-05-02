# arvis/kernel_core/syscalls/errors.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class SyscallError:
    code: str
    message: str
    retryable: bool = False
    metadata: dict[str, Any] | None = None

    def to_legacy_string(self) -> str:
        if self.message:
            return f"{self.code}:{self.message}"
        return self.code

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "metadata": self.metadata or {},
        }
