# arvis/kernel_core/vfs/zip/exceptions.py

from __future__ import annotations


class ZipIngestError(Exception):
    """Base class for ZIP ingest errors."""


class ZipRejectedError(ZipIngestError):
    """Raised when ZIP analysis rejects the archive."""


class ZipConflictError(ZipIngestError):
    """Raised when ZIP analysis detects VFS conflicts before execution."""
