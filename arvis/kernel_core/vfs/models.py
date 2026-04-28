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
    mime: str | None = None
    file_size: int | None = None
    created_at: int | None = None

    def is_file(self) -> bool:
        return self.item_type == "file"

    def is_folder(self) -> bool:
        return self.item_type == "folder"
