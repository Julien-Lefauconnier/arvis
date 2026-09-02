# tests/kernel_core/vfs/test_zip_unsupported_content.py
"""The analyzer's supported verdict governs the content import.

Campaign HARDEN (DM-H3, audit P1-15a, 2026-09-02). ZipAnalyzer marks
every file node ``supported`` (extension allow-list) with the reason
``unsupported_file_type`` when False, serializes both, and nothing
ever read them: the executor imported the content of every node all
the same. A computed-and-ignored safety field is worse than no field
(it documents a guarantee the code does not keep). Applied semantics:
an unsupported node keeps its VFS item (the tree stays faithful) but
its CONTENT is never handed to the importer, and the skip is recorded
under the analyzer's own reason.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer
from arvis.kernel_core.vfs.zip.collision import ZipCollisionService
from arvis.kernel_core.vfs.zip.executor import ZipExecutor
from arvis.kernel_core.vfs.zip.plan import ZipImportPlanService
from arvis.kernel_core.vfs.zip.service import ZipIngestService


class _RecordingImporter:
    """Content importer probe: records every file it is handed."""

    def __init__(self) -> None:
        self.imported: list[str] = []

    def import_file(self, *, file_path, user_id, vfs_item_id, zip_node) -> None:
        self.imported.append(zip_node.name)


def _make_zip(tmp_path: Path, files: dict[str, bytes]) -> Path:
    zip_path = tmp_path / "mixed.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return zip_path


def _build_service(importer: _RecordingImporter) -> tuple[VFSService, ZipIngestService]:
    repo = InMemoryVFSRepository()
    vfs = VFSService(repo)
    service = ZipIngestService(
        analyzer=ZipAnalyzer(),
        collision_service=ZipCollisionService(vfs),
        executor=ZipExecutor(vfs_service=vfs, content_importer=importer),
        planner=ZipImportPlanService(),
        vfs_service=vfs,
    )
    return vfs, service


def test_unsupported_content_is_skipped_not_imported(tmp_path) -> None:
    importer = _RecordingImporter()
    vfs, service = _build_service(importer)
    # .txt is on the analyzer's supported list; .xyz is not (and is
    # not on the guard's blocked list either, so it passes ingestion).
    zip_path = _make_zip(
        tmp_path,
        {"docs/a.txt": b"hello", "docs/weird.xyz": b"\x00\x01"},
    )

    result = service.execute_from_path(
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=None,
    )

    assert result["status"] == "completed"
    assert importer.imported == ["a.txt"], (
        "the analyzer marked weird.xyz supported=False and the executor "
        "handed its content to the importer anyway (DM-H3)"
    )
    skipped = {entry["name"]: entry["reason"] for entry in result["skipped_files"]}
    assert skipped.get("weird.xyz") == "unsupported_file_type"

    # The tree stays faithful: the item exists, only its content was
    # refused.
    names = sorted(item.display_name for item in vfs.list_items("u1"))
    assert names == ["a.txt", "docs", "weird.xyz"]
