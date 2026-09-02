# arvis/kernel_core/vfs/zip/executor.py

from __future__ import annotations

import os
import tempfile
from typing import Any, Protocol

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
        content_importer: ContentImporter | None = None,
    ) -> None:
        self.vfs = vfs_service
        self.content_importer = content_importer

    def execute(
        self,
        *,
        zip_root: ZipNode,
        zip_path: str,
        user_id: str,
        target_parent_id: str | None,
        keep_zip: bool = False,
    ) -> dict[str, Any]:
        created_count = 0
        imported_files: list[str] = []
        skipped_files: list[dict[str, str]] = []

        with ZipSafeReader(zip_path) as reader:

            def create_tree(node: ZipNode, parent_vfs_id: str | None) -> None:
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

        # DM-H1 (campaign HARDEN, audit P1-15d): the import used to
        # unlink zip_path here unless keep_zip was True. zip_path is a
        # HOST filesystem path received through a governed syscall
        # whose every other write goes through the VFS; deleting the
        # source archive is the host's act, never this executor's.
        # keep_zip is kept as an accepted no-op so signatures hold.

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
        # DM-H3 (campaign HARDEN, audit P1-15a): the analyzer's
        # supported verdict now governs the content import. The VFS
        # item was already created (the tree stays faithful); the
        # CONTENT of an unsupported entry is refused, recorded under
        # the reason the analyzer computed. Before this, the field was
        # computed, serialized and never read.
        if zip_node.supported is False:
            skipped_files.append(
                {
                    "name": zip_node.name,
                    "reason": zip_node.reason or "unsupported_file_type",
                }
            )
            return

        if self.content_importer is None:
            imported_files.append(zip_node.name)
            return

        if zip_node.zip_path is None:
            skipped_files.append({"name": zip_node.name, "reason": "missing_zip_path"})
            return

        tmp_path: str | None = None

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

        except Exception:  # arvis-broad: per-entry isolation of the batch import
            skipped_files.append(
                {"name": zip_node.name, "reason": "content_import_failed"}
            )

        finally:
            if tmp_path is not None and os.path.exists(tmp_path):
                os.unlink(tmp_path)
