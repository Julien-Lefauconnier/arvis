# arvis/runtime/__init__.py

"""
ARVIS runtime package.

IMPORTANT:
This package intentionally avoids importing heavy runtime
or pipeline modules at import-time in order to preserve
kernel dependency boundaries and avoid circular imports.
"""

__all__: list[str] = []
