# tests/kernel_core/vfs/test_zip_executor_host_fs.py
"""The governed ZIP import never touches the host filesystem source.

Campaign HARDEN (DM-H1, audit P1-15d, 2026-09-02). The executor used
to delete ``zip_path`` after a successful import unless the caller
passed ``keep_zip=True``: a host filesystem path, received through a
governed syscall whose every other write goes through the VFS,
unlinked by default outside any authorization layer. The source
archive belongs to the host; deleting it is the host's act. The
import must leave it untouched whatever ``keep_zip`` says (the
parameter is kept as an accepted no-op so signatures do not break).
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer
from arvis.kernel_core.vfs.zip.collision import ZipCollisionService
from arvis.kernel_core.vfs.zip.executor import ZipExecutor
from arvis.kernel_core.vfs.zip.plan import ZipImportPlanService
from arvis.kernel_core.vfs.zip.service import ZipIngestService


def _make_zip(tmp_path: Path, files: dict[str, bytes]) -> Path:
    zip_path = tmp_path / "source.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return zip_path


def _build_service() -> tuple[VFSService, ZipIngestService]:
    repo = InMemoryVFSRepository()
    vfs = VFSService(repo)
    service = ZipIngestService(
        analyzer=ZipAnalyzer(),
        collision_service=ZipCollisionService(vfs),
        executor=ZipExecutor(vfs_service=vfs),
        planner=ZipImportPlanService(),
        vfs_service=vfs,
    )
    return vfs, service


@pytest.mark.parametrize("keep_zip", [False, True])
def test_execute_never_unlinks_the_host_source(tmp_path, keep_zip) -> None:
    _, service = _build_service()
    zip_path = _make_zip(tmp_path, {"docs/a.txt": b"hello"})

    result = service.execute_from_path(
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=None,
        keep_zip=keep_zip,
    )

    assert result["status"] == "completed"
    assert zip_path.exists(), (
        "the governed import deleted the host source archive: the effect "
        "path must never unlink a host filesystem path (DM-H1)"
    )
