# arvis/reflexive/capabilities/capability.py

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Capability:
    key: str
    description: str
    enabled: bool
    limits: Tuple[str, ...]
