# arvis/host_api/vfs.py

"""The governed virtual file system surface.

The item model a host adapter translates its store into, and the
typed exceptions its routes are expected to handle.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.kernel_core.vfs.exceptions import (
    VFSCycleError,
    VFSError,
    VFSFolderNotEmptyError,
    VFSInvalidNameError,
    VFSItemNotFoundError,
    VFSNameConflictError,
    VFSParentNotFolderError,
    VFSParentNotFoundError,
)
from arvis.kernel_core.vfs.models import VFSItem

__all__ = [
    "VFSCycleError",
    "VFSError",
    "VFSFolderNotEmptyError",
    "VFSInvalidNameError",
    "VFSItem",
    "VFSItemNotFoundError",
    "VFSNameConflictError",
    "VFSParentNotFolderError",
    "VFSParentNotFoundError",
]
