# arvis/kernel_core/memory/exceptions.py

from __future__ import annotations


class MemoryError(Exception):
    """Base class for all kernel memory errors."""


class MemoryRecordNotFoundError(MemoryError):
    """Raised when the target memory record does not exist."""


class MemoryConflictError(MemoryError):
    """Raised when a conflicting memory record already exists."""


class MemoryInvalidNamespaceError(MemoryError):
    """Raised when a memory namespace is invalid."""


class MemoryInvalidKeyError(MemoryError):
    """Raised when a memory key is invalid."""


class MemoryInvalidTagsError(MemoryError):
    """Raised when provided tags are invalid."""


class MemoryRecordDeletedError(MemoryRecordNotFoundError):
    """Raised when a memory record existed but is now deleted."""
