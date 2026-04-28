# arvis/kernel_core/process/transitions.py

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from arvis.kernel_core.process.process import CognitiveProcess

from arvis.kernel_core.process.types import CognitiveProcessStatus


class InvalidTransitionError(Exception):
    pass


class ProcessTransitionManager:
    """
    Kernel-level authority for process state transitions.

    This enforces a strict state machine:
    no illegal transitions possible.
    """

    _VALID_TRANSITIONS = {
        CognitiveProcessStatus.READY: {
            CognitiveProcessStatus.RUNNING,
            CognitiveProcessStatus.SUSPENDED,
            CognitiveProcessStatus.ABORTED,
        },
        CognitiveProcessStatus.RUNNING: {
            CognitiveProcessStatus.READY,
            CognitiveProcessStatus.BLOCKED,
            CognitiveProcessStatus.WAITING_CONFIRMATION,
            CognitiveProcessStatus.SUSPENDED,
            CognitiveProcessStatus.COMPLETED,
            CognitiveProcessStatus.ABORTED,
        },
        CognitiveProcessStatus.BLOCKED: {
            CognitiveProcessStatus.READY,
            CognitiveProcessStatus.ABORTED,
        },
        CognitiveProcessStatus.WAITING_CONFIRMATION: {
            CognitiveProcessStatus.READY,
            CognitiveProcessStatus.ABORTED,
        },
        CognitiveProcessStatus.SUSPENDED: {
            CognitiveProcessStatus.READY,
            CognitiveProcessStatus.ABORTED,
        },
        CognitiveProcessStatus.COMPLETED: set(),
        CognitiveProcessStatus.ABORTED: set(),
    }

    @classmethod
    def transition(
        cls,
        process: CognitiveProcess,
        new_status: CognitiveProcessStatus,
    ) -> None:
        current = process.status

        # ----------------------------------------
        # IDENTITY TRANSITION (NO-OP)
        # ----------------------------------------
        if current == new_status:
            if hasattr(process, "metadata"):
                process.metadata.setdefault("transitions", []).append(
                    (current.value, new_status.value, "noop")
                )
            return

        allowed = cls._VALID_TRANSITIONS.get(current, set())

        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Invalid transition: {current.value} → {new_status.value}"
            )

        process.status = new_status
