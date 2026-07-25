# arvis/kernel_core/vfs/models.py

from __future__ import annotations

from dataclasses import dataclass, replace
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

    def _with_changes(self, **changes: object) -> VFSItem:
        """Return a copy with only the named fields changed, everything else
        PRESERVED (audit A-02). A mutation states what it changes; every
        security-bearing field it does not name (owner_id, organization_id,
        resource_scope) is carried over unchanged. Reconstructing a VFSItem
        field by field is the pattern that silently dropped resource_scope on
        rename and move; this makes that omission structurally impossible.
        Unknown field names raise (dataclasses.replace), so a typo cannot
        silently create a divergent object."""
        return replace(self, **changes)  # type: ignore[arg-type]
