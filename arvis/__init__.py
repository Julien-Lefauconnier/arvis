# arvis/__init__.py
"""
ARVIS — Adaptive Resilient Vigilant Intelligence System
"""

__version__ = "0.1.0"

from .api import *
from .api import __all__ as _api_all

__all__ = list(_api_all)