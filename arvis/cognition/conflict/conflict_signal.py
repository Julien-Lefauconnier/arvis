# arvis/cognition/conflict/conflict_signal.py

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .conflict_type import ConflictType


@dataclass(frozen=True)
class ConflictSignal:
    """
    Raw conflict signal emitted by the cognitive system.
    """

    type: ConflictType
    payload: Optional[Dict[str, Any]] = None
