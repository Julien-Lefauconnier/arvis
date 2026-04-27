# arvis/__init__.py
"""
ARVIS — Deterministic Cognitive Runtime for Reliable AI Systems.

Top-level package export.
Public users should be able to do:

    import arvis
    os = arvis.CognitiveOS()

or

    from arvis import CognitiveOS
"""

from .api import *  # noqa: F401,F403
from .api import __all__ as _api_all

__all__ = list(_api_all)