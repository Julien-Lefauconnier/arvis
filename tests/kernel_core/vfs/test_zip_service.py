# tests/kernel_core/vfs/test_zip_service.py

from __future__ import annotations

import zipfile

from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer
from arvis.kernel_core.vfs.zip.collision import ZipCollisionService
from arvis.kernel_core.vfs.zip.executor import ZipExecutor
from arvis.kernel_core.vfs.zip.plan import ZipImportPlanService
from arvis.kernel_core.vfs.zip.service import ZipIngestService


def _make_zip(tmp_path, files: dict[str, bytes]):
    zip_path = tmp_path / "test.zip"
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


def test_zip_service_analyze_ready(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENV", "test")

    _, service = _build_service()
    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
            "docs/b.md": b"# test",
        },
    )

    decision = service.analyze_and_validate(
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=None,
    )

    assert decision.status == "ready"
    assert decision.zip_root is not None
    assert decision.collisions is None


def test_zip_service_analyze_conflict(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENV", "test")

    vfs, service = _build_service()
    vfs.create_file_item(
        user_id="u1",
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    zip_path = _make_zip(
        tmp_path,
        {
            "a.txt": b"hello",
        },
    )

    decision = service.analyze_and_validate(
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=None,
    )

    assert decision.status == "conflict"
    assert decision.collisions is not None
    assert decision.collisions.has_conflicts is True


def test_zip_service_execute_import(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENV", "test")

    vfs, service = _build_service()
    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
            "docs/b.md": b"# test",
        },
    )

    decision = service.analyze_and_validate(
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=None,
    )

    assert decision.status == "ready"
    assert decision.zip_root is not None

    result = service.execute_import(
        zip_root=decision.zip_root,
        zip_path=str(zip_path),
        user_id="u1",
        target_parent_id=None,
        keep_zip=True,
    )

    assert result["status"] == "completed"
    assert result["created_items"] == 3
    assert sorted(result["imported_files"]) == ["a.txt", "b.md"]

    items = vfs.list_items("u1")
    names = sorted(item.display_name for item in items)
    assert names == ["a.txt", "b.md", "docs"]