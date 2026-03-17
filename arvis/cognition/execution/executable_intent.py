# arvis/cognition/execution/executable_intent.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class ExecutableIntent:
    """
    ZKCS-compliant executable contract.

    Kernel invariants:
    - immutable
    - no raw user input
    - no document content
    - execution-only
    """

    bundle_id: str
    user_id: str

    # opaque intent (non-linguistic)
    intent_signature: str

    # execution constraints
    allow_rag: bool
    max_top_k: int
    provider: str

    decided_at: datetime

    # optional safe context for realization
    linguistic_context: Optional[Dict[str, Any]] = None