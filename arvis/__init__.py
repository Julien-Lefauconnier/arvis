# arvis/__init__.py
"""
ARVIS Cognitive OS — Public API root.
"""

from .api import *  # noqa: F401,F403

from .api import __all__ as _api_all

__all__ = list(_api_all)