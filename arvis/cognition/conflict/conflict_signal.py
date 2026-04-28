# arvis/cognition/conflict/conflict_signal.py

from dataclasses import dataclass
from typing import Any

from .conflict_type import ConflictType


@dataclass(frozen=True)
class ConflictSignal:
    """
    Raw conflict signal emitted by the cognitive system.
    """

    type: ConflictType
    payload: dict[str, Any] | None = None
