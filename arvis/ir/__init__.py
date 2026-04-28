# arvis/ir/__init__.py

"""
ARVIS Cognitive IR (Intermediate Representation)

Versioned, immutable, transport-safe representation
of cognitive processes inside the ARVIS kernel.
"""

from .version import IR_FINGERPRINT, IR_VERSION

__all__ = [
    "IR_VERSION",
    "IR_FINGERPRINT",
]
