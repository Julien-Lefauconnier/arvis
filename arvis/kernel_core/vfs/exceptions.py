# arvis/kernel_core/vfs/exceptions.py

from __future__ import annotations


class VFSError(Exception):
    """Base class for all VFS domain errors."""


class VFSItemNotFoundError(VFSError):
    """Raised when the target item does not exist."""


class VFSParentNotFoundError(VFSError):
    """Raised when the target parent folder does not exist."""


class VFSParentNotFolderError(VFSError):
    """Raised when the target parent exists but is not a folder."""


class VFSNameConflictError(VFSError):
    """
    Raised when another item with the same name already exists
    in the target folder.
    """


class VFSFolderNotEmptyError(VFSError):
    """Raised when attempting to delete a non-empty folder."""


class VFSCycleError(VFSError):
    """Raised when moving a folder into itself or one of its descendants."""


class VFSInvalidNameError(VFSError):
    """Raised when a provided item name is invalid."""
