# arvis/reflexive/capabilities/capability.py

from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    key: str
    description: str
    enabled: bool
    limits: tuple[str, ...]
