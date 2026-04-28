# arvis/kernel_core/vfs/repository.py

from __future__ import annotations

from typing import Protocol

from arvis.kernel_core.vfs.models import VFSItem


class VFSRepository(Protocol):
    def list_items(self, user_id: str) -> list[VFSItem]: ...

    def get_item(self, user_id: str, item_id: str) -> VFSItem | None: ...

    def create_folder(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: str | None,
    ) -> str: ...

    def create_file_item(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: str | None,
        size: int | None,
        mime: str | None,
    ) -> str: ...

    def delete_item(
        self,
        *,
        user_id: str,
        item_id: str,
    ) -> None: ...

    def rename_item(
        self,
        *,
        user_id: str,
        item_id: str,
        new_name: str,
    ) -> None: ...

    def move_item(
        self,
        *,
        user_id: str,
        item_id: str,
        parent_id: str | None,
    ) -> None: ...
