# arvis/cognition/bundle/__init__.py
"""
Cognitive bundle structures.

A CognitiveBundle is a declarative snapshot of the cognitive
state produced by the kernel.
"""

from .cognitive_bundle_builder import CognitiveBundleBuilder
from .cognitive_bundle_snapshot import CognitiveBundleSnapshot

__all__ = [
    "CognitiveBundleSnapshot",
    "CognitiveBundleBuilder",
]
