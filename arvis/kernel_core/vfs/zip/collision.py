# arvis/kernel_core/vfs/zip/collision.py

from __future__ import annotations

from typing import Optional

from arvis.kernel_core.vfs.models import VFSItem
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.models import (
    ZipCollision,
    ZipCollisionReport,
    ZipNode,
)


class ZipCollisionService:
    """
    Detect collisions between a ZIP tree and the current VFS state.
    """

    def __init__(self, vfs_service: VFSService):
        self.vfs = vfs_service

    def detect(
        self,
        *,
        zip_root: ZipNode,
        user_id: str,
        target_parent_id: Optional[str],
    ) -> ZipCollisionReport:
        vfs_items = self.vfs.list_items(user_id)

        items_by_id: dict[str, VFSItem] = {item.item_id: item for item in vfs_items}
        children_by_parent_and_name: dict[Optional[str], dict[str, VFSItem]] = {}

        for item in vfs_items:
            children_by_parent_and_name.setdefault(item.parent_id, {})[
                item.display_name
            ] = item

        collisions: list[ZipCollision] = []

        def walk(zip_node: ZipNode, parent_vfs_id: Optional[str]) -> None:
            if zip_node.parent is None:
                for child in zip_node.children:
                    walk(child, parent_vfs_id)
                return

            if parent_vfs_id is not None:
                parent_item = items_by_id.get(parent_vfs_id)
                if parent_item is not None and parent_item.is_file():
                    collisions.append(
                        ZipCollision(
                            zip_node=zip_node,
                            vfs_item=parent_item,
                            reason="parent_is_file",
                        )
                    )
                    return

            siblings = children_by_parent_and_name.get(parent_vfs_id, {})
            existing = siblings.get(zip_node.name)

            if existing is not None:
                collisions.append(
                    ZipCollision(
                        zip_node=zip_node,
                        vfs_item=existing,
                        reason="already_exists",
                    )
                )

            next_parent_id = (
                existing.item_id
                if (existing is not None and existing.is_folder())
                else parent_vfs_id
            )

            for child in zip_node.children:
                walk(child, next_parent_id)

        walk(zip_root, target_parent_id)

        return ZipCollisionReport(
            has_conflicts=bool(collisions),
            collisions=collisions,
        )
