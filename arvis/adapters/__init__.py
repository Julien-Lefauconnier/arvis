# arvis/adapters/__init__.py
"""
ARVIS adapters package.
"""

from .registry import get_llm_adapter

__all__ = [
    "get_llm_adapter",
]
