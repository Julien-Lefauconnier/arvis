# arvis/kernel_core/vfs/repositories/in_memory.py

from __future__ import annotations

import time
import uuid
from typing import Optional

from arvis.kernel_core.vfs.models import VFSItem


class InMemoryVFSRepository:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, VFSItem]] = {}

    def _user_bucket(self, user_id: str) -> dict[str, VFSItem]:
        return self._store.setdefault(user_id, {})

    def list_items(self, user_id: str) -> list[VFSItem]:
        bucket = self._user_bucket(user_id)
        return list(bucket.values())

    def get_item(self, user_id: str, item_id: str) -> Optional[VFSItem]:
        bucket = self._user_bucket(user_id)
        return bucket.get(item_id)

    def create_folder(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: Optional[str],
    ) -> str:
        bucket = self._user_bucket(user_id)
        item_id = str(uuid.uuid4())
        bucket[item_id] = VFSItem(
            item_id=item_id,
            display_name=name,
            item_type="folder",
            parent_id=parent_id,
            mime=None,
            file_size=0,
            created_at=int(time.time()),
        )
        return item_id

    def create_file_item(
        self,
        *,
        user_id: str,
        name: str,
        parent_id: Optional[str],
        size: Optional[int],
        mime: Optional[str],
    ) -> str:
        bucket = self._user_bucket(user_id)
        item_id = str(uuid.uuid4())
        bucket[item_id] = VFSItem(
            item_id=item_id,
            display_name=name,
            item_type="file",
            parent_id=parent_id,
            mime=mime,
            file_size=size,
            created_at=int(time.time()),
        )
        return item_id

    def delete_item(
        self,
        *,
        user_id: str,
        item_id: str,
    ) -> None:
        bucket = self._user_bucket(user_id)
        bucket.pop(item_id, None)

    def rename_item(
        self,
        *,
        user_id: str,
        item_id: str,
        new_name: str,
    ) -> None:
        bucket = self._user_bucket(user_id)
        item = bucket[item_id]
        bucket[item_id] = VFSItem(
            item_id=item.item_id,
            display_name=new_name,
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
        parent_id: Optional[str],
    ) -> None:
        bucket = self._user_bucket(user_id)
        item = bucket[item_id]
        bucket[item_id] = VFSItem(
            item_id=item.item_id,
            display_name=item.display_name,
            item_type=item.item_type,
            parent_id=parent_id,
            mime=item.mime,
            file_size=item.file_size,
            created_at=item.created_at,
        )
