# arvis/kernel_core/vfs/repository.py

from __future__ import annotations

from typing import Protocol

from arvis.kernel_core.vfs.models import VFSItem


class VFSRepository(Protocol):
    """Persistence contract used by :class:`VFSService`.

    Host implementations are part of the VFS trust boundary. Creation must
    persist the supplied organization and resource scope atomically with the
    item, and delete/get must provide reliable read-after-delete semantics for
    compensating rollback verification.
    """

    def list_items(self, user_id: str) -> list[VFSItem]: ...

    def get_item(self, user_id: str, item_id: str) -> VFSItem | None: ...

    def create_folder(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: str | None,
        organization_id: str | None = None,
        resource_scope: str | None = None,
    ) -> str: ...

    def create_file_item(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: str | None,
        size: int | None,
        mime: str | None,
        organization_id: str | None = None,
        resource_scope: str | None = None,
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
