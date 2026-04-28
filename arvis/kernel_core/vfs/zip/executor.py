# arvis/kernel_core/vfs/zip/executor.py

from __future__ import annotations

import os
import tempfile
from typing import Any, Optional, Protocol

from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.models import ZipNode
from arvis.kernel_core.vfs.zip.reader import ZipSafeReader


class ContentImporter(Protocol):
    def import_file(
        self,
        *,
        file_path: str,
        user_id: str,
        vfs_item_id: str,
        zip_node: ZipNode,
    ) -> Any: ...


class ZipExecutor:
    """
    Execute a validated ZIP import in a VFS-first manner.

    Responsibilities:
    - create folders in VFS
    - create file items in VFS
    - optionally delegate content import if a content importer is provided
    """

    def __init__(
        self,
        vfs_service: VFSService,
        content_importer: Optional[ContentImporter] = None,
    ) -> None:
        self.vfs = vfs_service
        self.content_importer = content_importer

    def execute(
        self,
        *,
        zip_root: ZipNode,
        zip_path: str,
        user_id: str,
        target_parent_id: Optional[str],
        keep_zip: bool = False,
    ) -> dict[str, Any]:
        created_count = 0
        imported_files: list[str] = []
        skipped_files: list[dict[str, str]] = []

        with ZipSafeReader(zip_path) as reader:

            def create_tree(node: ZipNode, parent_vfs_id: Optional[str]) -> None:
                nonlocal created_count

                if node.parent is not None:
                    if node.is_folder():
                        created = self.vfs.create_folder(
                            user_id=user_id,
                            name=node.name,
                            parent_id=parent_vfs_id,
                        )
                        created_count += 1
                        parent_vfs_id = created.item_id

                    elif node.is_file():
                        created = self.vfs.create_file_item(
                            user_id=user_id,
                            name=node.name,
                            parent_id=parent_vfs_id,
                            size=node.size,
                            mime=None,
                        )
                        created_count += 1

                        self._optionally_import_file(
                            reader=reader,
                            zip_node=node,
                            vfs_item_id=created.item_id,
                            user_id=user_id,
                            imported_files=imported_files,
                            skipped_files=skipped_files,
                        )
                        return

                for child in node.children:
                    create_tree(child, parent_vfs_id)

            create_tree(zip_root, target_parent_id)

        if not keep_zip and os.path.exists(zip_path):
            os.unlink(zip_path)

        return {
            "status": "completed",
            "imported_files": imported_files,
            "skipped_files": skipped_files,
            "created_items": created_count,
        }

    def _optionally_import_file(
        self,
        *,
        reader: ZipSafeReader,
        zip_node: ZipNode,
        vfs_item_id: str,
        user_id: str,
        imported_files: list[str],
        skipped_files: list[dict[str, str]],
    ) -> None:
        if self.content_importer is None:
            imported_files.append(zip_node.name)
            return

        if zip_node.zip_path is None:
            skipped_files.append({"name": zip_node.name, "reason": "missing_zip_path"})
            return

        tmp_path: Optional[str] = None

        try:
            with reader.open_file(zip_node.zip_path) as raw:
                with tempfile.NamedTemporaryFile(delete=False) as tmp:
                    tmp.write(raw.read())
                    tmp_path = tmp.name

            self.content_importer.import_file(
                file_path=tmp_path,
                user_id=user_id,
                vfs_item_id=vfs_item_id,
                zip_node=zip_node,
            )

            imported_files.append(zip_node.name)

        except Exception:
            skipped_files.append(
                {"name": zip_node.name, "reason": "content_import_failed"}
            )

        finally:
            if tmp_path is not None and os.path.exists(tmp_path):
                os.unlink(tmp_path)
