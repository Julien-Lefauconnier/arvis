# arvis/kernel_core/vfs/service.py

from __future__ import annotations

from arvis.kernel_core.vfs.exceptions import (
    VFSCycleError,
    VFSFolderNotEmptyError,
    VFSInvalidNameError,
    VFSItemNotFoundError,
    VFSNameConflictError,
    VFSParentNotFolderError,
    VFSParentNotFoundError,
)
from arvis.kernel_core.vfs.models import VFSItem
from arvis.kernel_core.vfs.repository import VFSRepository


class VFSService:
    def __init__(self, repo: VFSRepository):
        self.repo = repo

    def list_items(self, user_id: str) -> list[VFSItem]:
        return self.repo.list_items(user_id)

    def get_item(self, *, user_id: str, item_id: str) -> VFSItem:
        item = self.repo.get_item(user_id, item_id)
        if item is None:
            raise VFSItemNotFoundError(f"item not found: {item_id}")
        return item

    def create_folder(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: str | None,
    ) -> VFSItem:
        normalized_name = self._normalize_name(name)
        items = self.repo.list_items(user_id)

        self._validate_parent(items, parent_id)
        self._ensure_name_available(
            items=items,
            parent_id=parent_id,
            display_name=normalized_name,
        )

        folder_id = self.repo.create_folder(
            user_id=user_id,
            name=normalized_name,
            parent_id=parent_id,
        )

        created = self.repo.get_item(user_id, folder_id)
        if created is not None:
            return created

        return VFSItem(
            item_id=folder_id,
            display_name=normalized_name,
            item_type="folder",
            parent_id=parent_id,
            mime=None,
            file_size=0,
            created_at=None,
        )

    def create_file_item(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: str | None,
        size: int | None,
        mime: str | None = None,
    ) -> VFSItem:
        normalized_name = self._normalize_name(name)
        items = self.repo.list_items(user_id)

        self._validate_parent(items, parent_id)
        self._ensure_name_available(
            items=items,
            parent_id=parent_id,
            display_name=normalized_name,
        )

        file_id = self.repo.create_file_item(
            user_id=user_id,
            name=normalized_name,
            parent_id=parent_id,
            size=size,
            mime=mime,
        )

        created = self.repo.get_item(user_id, file_id)
        if created is not None:
            return created

        return VFSItem(
            item_id=file_id,
            display_name=normalized_name,
            item_type="file",
            parent_id=parent_id,
            mime=mime,
            file_size=size,
            created_at=None,
        )

    def delete_item(
        self,
        *,
        user_id: str,
        item_id: str,
    ) -> None:
        items = self.repo.list_items(user_id)
        item = self._find_item(items, item_id)

        if item.is_folder():
            has_children = any(i.parent_id == item_id for i in items)
            if has_children:
                raise VFSFolderNotEmptyError(f"folder not empty: {item_id}")

        self.repo.delete_item(
            user_id=user_id,
            item_id=item_id,
        )

    def rename_item(
        self,
        *,
        user_id: str,
        item_id: str,
        new_name: str,
    ) -> VFSItem:
        normalized_name = self._normalize_name(new_name)
        items = self.repo.list_items(user_id)
        item = self._find_item(items, item_id)

        self._ensure_name_available(
            items=items,
            parent_id=item.parent_id,
            display_name=normalized_name,
            exclude_item_id=item_id,
        )

        self.repo.rename_item(
            user_id=user_id,
            item_id=item_id,
            new_name=normalized_name,
        )

        updated = self.repo.get_item(user_id, item_id)
        if updated is not None:
            return updated

        return VFSItem(
            item_id=item.item_id,
            display_name=normalized_name,
            item_type=item.item_type,
            parent_id=item.parent_id,
            mime=item.mime,
            file_size=item.file_size,
            created_at=item.created_at,
        )

    def move_item(
        self,
        *,
        user_id: str,
        item_id: str,
        parent_id: str | None,
    ) -> VFSItem:
        items = self.repo.list_items(user_id)
        item = self._find_item(items, item_id)

        if parent_id is not None:
            parent = self._find_item(items, parent_id, parent=True)
            if not parent.is_folder():
                raise VFSParentNotFolderError(f"parent is not a folder: {parent_id}")

        if item.is_folder() and parent_id is not None:
            descendants = self._collect_descendants(items, item.item_id)
            if parent_id == item.item_id or parent_id in descendants:
                raise VFSCycleError("cannot move folder into itself or a descendant")

        self._ensure_name_available(
            items=items,
            parent_id=parent_id,
            display_name=item.display_name,
            exclude_item_id=item.item_id,
        )

        self.repo.move_item(
            user_id=user_id,
            item_id=item.item_id,
            parent_id=parent_id,
        )

        updated = self.repo.get_item(user_id, item_id)
        if updated is not None:
            return updated

        return VFSItem(
            item_id=item.item_id,
            display_name=item.display_name,
            item_type=item.item_type,
            parent_id=parent_id,
            mime=item.mime,
            file_size=item.file_size,
            created_at=item.created_at,
        )

    def _normalize_name(self, name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise VFSInvalidNameError("name cannot be empty")
        return normalized

    def _validate_parent(
        self,
        items: list[VFSItem],
        parent_id: str | None,
    ) -> None:
        if parent_id is None:
            return

        parent = next((i for i in items if i.item_id == parent_id), None)
        if parent is None:
            raise VFSParentNotFoundError(f"parent folder not found: {parent_id}")

        if not parent.is_folder():
            raise VFSParentNotFolderError(f"parent is not a folder: {parent_id}")

    def _ensure_name_available(
        self,
        *,
        items: list[VFSItem],
        parent_id: str | None,
        display_name: str,
        exclude_item_id: str | None = None,
    ) -> None:
        for item in items:
            if exclude_item_id is not None and item.item_id == exclude_item_id:
                continue

            if item.parent_id == parent_id and item.display_name == display_name:
                raise VFSNameConflictError(
                    f"item already exists in target folder: {display_name}"
                )

    def _find_item(
        self,
        items: list[VFSItem],
        item_id: str,
        parent: bool = False,
    ) -> VFSItem:
        item = next((i for i in items if i.item_id == item_id), None)
        if item is None:
            if parent:
                raise VFSParentNotFoundError(f"parent folder not found: {item_id}")
            raise VFSItemNotFoundError(f"item not found: {item_id}")
        return item

    def _collect_descendants(
        self,
        items: list[VFSItem],
        root_item_id: str,
    ) -> set[str]:
        descendants: set[str] = set()
        stack = [root_item_id]

        while stack:
            current = stack.pop()
            for item in items:
                if item.parent_id == current and item.item_id not in descendants:
                    descendants.add(item.item_id)
                    stack.append(item.item_id)

        return descendants
