# tests/kernel_core/vfs/test_zip_collision.py

from __future__ import annotations

from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.collision import ZipCollisionService
from arvis.kernel_core.vfs.zip.models import ZipNode


def _file(name: str, path: str | None = None) -> ZipNode:
    return ZipNode(
        name=name,
        node_type="file",
        zip_path=path or name,
    )


def _folder(name: str) -> ZipNode:
    return ZipNode(
        name=name,
        node_type="folder",
    )


def test_zip_collision_detects_existing_item() -> None:
    repo = InMemoryVFSRepository()
    vfs = VFSService(repo)
    user_id = "u1"

    vfs.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    root = ZipNode(name="/", node_type="folder")
    root.add_child(_file("a.txt", "a.txt"))

    service = ZipCollisionService(vfs)
    report = service.detect(
        zip_root=root,
        user_id=user_id,
        target_parent_id=None,
    )

    assert report.has_conflicts is True
    assert len(report.collisions) == 1
    assert report.collisions[0].reason == "already_exists"


def test_zip_collision_no_conflict_when_target_is_empty() -> None:
    repo = InMemoryVFSRepository()
    vfs = VFSService(repo)
    user_id = "u1"

    root = ZipNode(name="/", node_type="folder")
    root.add_child(_file("a.txt", "a.txt"))

    service = ZipCollisionService(vfs)
    report = service.detect(
        zip_root=root,
        user_id=user_id,
        target_parent_id=None,
    )

    assert report.has_conflicts is False
    assert report.collisions == []


def test_zip_collision_detects_nested_existing_folder_entry() -> None:
    repo = InMemoryVFSRepository()
    vfs = VFSService(repo)
    user_id = "u1"

    docs = vfs.create_folder(
        user_id=user_id,
        name="docs",
        parent_id=None,
    )
    vfs.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=docs.item_id,
        size=1,
        mime="text/plain",
    )

    root = ZipNode(name="/", node_type="folder")
    docs_zip = _folder("docs")
    docs_zip.add_child(_file("a.txt", "docs/a.txt"))
    root.add_child(docs_zip)

    service = ZipCollisionService(vfs)
    report = service.detect(
        zip_root=root,
        user_id=user_id,
        target_parent_id=None,
    )

    assert report.has_conflicts is True
    assert any(c.reason == "already_exists" for c in report.collisions)