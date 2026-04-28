# arvis/kernel_core/syscalls/artifact.py

from __future__ import annotations

from typing import Any, Dict, Optional


class ExecutionArtifact:
    def __init__(
        self,
        *,
        artifact_type: str,
        syscall: str,
        status: str,
        output: Optional[Any] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        replay_policy: str = "unknown",
        process_id: Optional[str] = None,
        tick: Optional[int] = None,
        timestamp: Optional[float] = None,
        causal_id: Optional[str] = None,
    ) -> None:
        self.metadata: Dict[str, Any] = metadata or {}

        self.id: str = causal_id or self._build_id(
            syscall=syscall,
            process_id=process_id,
            tick=tick,
            seq=self.metadata.get("seq"),
        )

        self.artifact_type: str = artifact_type
        self.syscall: str = syscall
        self.status: str = status  # "success" | "error"

        # HARDENING: enforce valid status
        if self.status not in ("success", "error"):
            raise ValueError(f"invalid artifact status: {self.status}")

        # HARDENING: enforce consistency
        if self.status == "success" and error is not None:
            raise ValueError("success artifact cannot have error")

        if self.status == "error" and not error:
            raise ValueError("error artifact must have error message")

        self.output: Optional[Any] = output
        self.error: Optional[str] = error

        self.metadata = self.metadata

        self.replay_policy: str = replay_policy

        self.process_id: Optional[str] = process_id
        self.tick: Optional[int] = tick

        if timestamp is None:
            raise RuntimeError(
                "artifact requires explicit timestamp (kernel-controlled)"
            )

        self.timestamp: float = float(timestamp)

    # -------------------------
    # deterministic id
    # -------------------------

    @staticmethod
    def _build_id(
        *,
        syscall: str,
        process_id: Optional[str],
        tick: Optional[int],
        seq: Optional[int],
    ) -> str:
        return f"artifact:{syscall}:{process_id or 'none'}:{tick or 0}:{seq or 0}"

    # -------------------------
    # helpers
    # -------------------------

    @property
    def success(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "causal_id": self.id,
            "type": self.artifact_type,
            "syscall": self.syscall,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata,
            "replay_policy": self.replay_policy,
            "process_id": self.process_id,
            "tick": self.tick,
            "timestamp": self.timestamp,
        }
