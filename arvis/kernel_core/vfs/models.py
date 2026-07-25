# arvis/kernel_core/vfs/models.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VFSItemType = Literal["file", "folder"]


@dataclass(frozen=True)
class VFSItem:
    item_id: str
    display_name: str
    item_type: VFSItemType
    parent_id: str | None
    owner_id: str
    organization_id: str | None = None
    mime: str | None = None
    file_size: int | None = None
    created_at: int | None = None
    # Opaque narrower-than-organization scope of this item (a matter, a
    # project, whatever the host layer names it). ARVIS never parses it: the
    # item resolver copies it verbatim into the AccessContext, where the
    # injected scope rule decides coverage. None means the item is not
    # sub-scoped, the behaviour every item had before scoped grants existed.
    # LAST in the field order (audit A-01): appending it keeps every 0.1.0b2
    # positional constructor call producing the exact same object, while new
    # hosts pass the scope by keyword.
    resource_scope: str | None = None

    def is_file(self) -> bool:
        return self.item_type == "file"

    def is_folder(self) -> bool:
        return self.item_type == "folder"
