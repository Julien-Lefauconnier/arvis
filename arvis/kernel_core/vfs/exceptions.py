# arvis/kernel_core/vfs/exceptions.py

from __future__ import annotations

from arvis.errors import ArvisDomainError


class VFSError(ArvisDomainError):
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


class VFSInheritanceViolationError(VFSError):
    """Raised when a created item does not carry its parent's security context.

    Creation inheritance (organization and scope) is imposed AND verified by
    the service, the common boundary of every creation path (audit A-06,
    counter-audit B3-VFS-02). If the repository returns an item that does not
    carry the parent's organization and scope, the service rolls the item back
    and raises this. It is a security defect, not an ordinary VFS condition,
    and the syscall body maps it to a fail-closed security refusal, never to a
    routine VFS error code."""
