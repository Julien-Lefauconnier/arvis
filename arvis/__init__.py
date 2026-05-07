# arvis/__init__.py
"""
Top-level public API.

Only stable high-level entrypoints are exposed here.
"""

from .api.engine import ArvisEngine
from .api.os import CognitiveOS, CognitiveOSConfig

__all__ = [
    "ArvisEngine",
    "CognitiveOS",
    "CognitiveOSConfig",
]
