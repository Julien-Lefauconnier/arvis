# arvis/control/__init__.py
"""
Control primitives.

Provides control mechanisms for stabilizing cognitive
regimes and preventing oscillatory behavior.
"""

from .control_inertia import ControlInertia

__all__ = [
    "ControlInertia",
]