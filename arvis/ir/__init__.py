# arvis/ir/__init__.py

"""
ARVIS Cognitive IR (Intermediate Representation)

Versioned, immutable, transport-safe representation
of cognitive processes inside the ARVIS kernel.
"""

from .version import IR_VERSION, IR_FINGERPRINT

__all__ = [
    "IR_VERSION",
    "IR_FINGERPRINT",
]
