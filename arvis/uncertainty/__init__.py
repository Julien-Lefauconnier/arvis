# arvis/uncertainty/__init__.py
"""
Uncertainty modeling primitives.

Defines the uncertainty dimensions and frames used
to characterize fragile reasoning situations.
"""

from .uncertainty_axis import UncertaintyAxis
from .uncertainty_frame import UncertaintyFrame
from .uncertainty_frame_registry import UncertaintyFrameRegistry

__all__ = [
    "UncertaintyAxis",
    "UncertaintyFrame",
    "UncertaintyFrameRegistry",
]
