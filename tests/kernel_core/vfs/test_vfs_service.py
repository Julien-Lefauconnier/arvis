# tests/kernel_core/vfs/test_vfs_service.py

from __future__ import annotations

import pytest

from arvis.kernel_core.vfs.exceptions import (
    VFSCycleError,
    VFSFolderNotEmptyError,
    VFSInvalidNameError,
    VFSItemNotFoundError,
    VFSNameConflictError,
    VFSParentNotFolderError,
    VFSParentNotFoundError,
)
from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService


@pytest.fixture
def repo() -> InMemoryVFSRepository:
    return InMemoryVFSRepository()


@pytest.fixture
def service(repo: InMemoryVFSRepository) -> VFSService:
    return VFSService(repo)


@pytest.fixture
def user_id() -> str:
    return "user-1"


def test_list_items_empty(service: VFSService, user_id: str) -> None:
    assert service.list_items(user_id) == []


def test_get_item_not_found(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSItemNotFoundError):
        service.get_item(user_id=user_id, item_id="missing")


def test_create_folder_root(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )

    assert folder.display_name == "Docs"
    assert folder.item_type == "folder"
    assert folder.parent_id is None
    assert folder.is_folder() is True


def test_create_folder_strips_name(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="  Docs  ",
        parent_id=None,
    )

    assert folder.display_name == "Docs"


def test_create_folder_empty_name(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSInvalidNameError):
        service.create_folder(
            user_id=user_id,
            name="   ",
            parent_id=None,
        )


def test_create_folder_with_valid_parent(service: VFSService, user_id: str) -> None:
    parent = service.create_folder(
        user_id=user_id,
        name="Root",
        parent_id=None,
    )

    child = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=parent.item_id,
    )

    assert child.parent_id == parent.item_id
    assert child.item_type == "folder"


def test_create_folder_parent_not_found(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSParentNotFoundError):
        service.create_folder(
            user_id=user_id,
            name="Docs",
            parent_id="missing-parent",
        )


def test_create_folder_parent_is_file(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=10,
        mime="text/plain",
    )

    with pytest.raises(VFSParentNotFolderError):
        service.create_folder(
            user_id=user_id,
            name="Docs",
            parent_id=file_item.item_id,
        )


def test_create_folder_name_conflict_with_folder(service: VFSService, user_id: str) -> None:
    service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )

    with pytest.raises(VFSNameConflictError):
        service.create_folder(
            user_id=user_id,
            name="Docs",
            parent_id=None,
        )


def test_create_folder_name_conflict_with_file(service: VFSService, user_id: str) -> None:
    service.create_file_item(
        user_id=user_id,
        name="Docs",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSNameConflictError):
        service.create_folder(
            user_id=user_id,
            name="Docs",
            parent_id=None,
        )


def test_create_file_root(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="note.txt",
        parent_id=None,
        size=12,
        mime="text/plain",
    )

    assert file_item.display_name == "note.txt"
    assert file_item.item_type == "file"
    assert file_item.parent_id is None
    assert file_item.mime == "text/plain"
    assert file_item.file_size == 12
    assert file_item.is_file() is True


def test_create_file_strips_name(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="  note.txt  ",
        parent_id=None,
        size=12,
        mime="text/plain",
    )

    assert file_item.display_name == "note.txt"


def test_create_file_empty_name(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSInvalidNameError):
        service.create_file_item(
            user_id=user_id,
            name="   ",
            parent_id=None,
            size=1,
            mime="text/plain",
        )


def test_create_file_with_valid_parent(service: VFSService, user_id: str) -> None:
    parent = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )

    file_item = service.create_file_item(
        user_id=user_id,
        name="readme.md",
        parent_id=parent.item_id,
        size=42,
        mime="text/markdown",
    )

    assert file_item.parent_id == parent.item_id
    assert file_item.item_type == "file"


def test_create_file_parent_not_found(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSParentNotFoundError):
        service.create_file_item(
            user_id=user_id,
            name="a.txt",
            parent_id="missing-parent",
            size=1,
            mime="text/plain",
        )


def test_create_file_parent_is_file(service: VFSService, user_id: str) -> None:
    parent_file = service.create_file_item(
        user_id=user_id,
        name="parent.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSParentNotFolderError):
        service.create_file_item(
            user_id=user_id,
            name="child.txt",
            parent_id=parent_file.item_id,
            size=1,
            mime="text/plain",
        )


def test_create_file_name_conflict(service: VFSService, user_id: str) -> None:
    service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSNameConflictError):
        service.create_file_item(
            user_id=user_id,
            name="a.txt",
            parent_id=None,
            size=2,
            mime="text/plain",
        )


def test_delete_file_ok(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    service.delete_item(
        user_id=user_id,
        item_id=file_item.item_id,
    )

    with pytest.raises(VFSItemNotFoundError):
        service.get_item(user_id=user_id, item_id=file_item.item_id)


def test_delete_empty_folder_ok(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )

    service.delete_item(
        user_id=user_id,
        item_id=folder.item_id,
    )

    with pytest.raises(VFSItemNotFoundError):
        service.get_item(user_id=user_id, item_id=folder.item_id)


def test_delete_non_empty_folder_blocked(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )
    service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=folder.item_id,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSFolderNotEmptyError):
        service.delete_item(
            user_id=user_id,
            item_id=folder.item_id,
        )


def test_delete_missing_item(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSItemNotFoundError):
        service.delete_item(
            user_id=user_id,
            item_id="missing",
        )


def test_rename_item_ok(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="old.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    renamed = service.rename_item(
        user_id=user_id,
        item_id=file_item.item_id,
        new_name="new.txt",
    )

    assert renamed.display_name == "new.txt"
    assert renamed.item_id == file_item.item_id


def test_rename_item_strips_name(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="old.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    renamed = service.rename_item(
        user_id=user_id,
        item_id=file_item.item_id,
        new_name="  new.txt  ",
    )

    assert renamed.display_name == "new.txt"


def test_rename_item_empty_name(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="old.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSInvalidNameError):
        service.rename_item(
            user_id=user_id,
            item_id=file_item.item_id,
            new_name="   ",
        )


def test_rename_item_missing(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSItemNotFoundError):
        service.rename_item(
            user_id=user_id,
            item_id="missing",
            new_name="x.txt",
        )


def test_rename_item_conflict(service: VFSService, user_id: str) -> None:
    a = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )
    service.create_file_item(
        user_id=user_id,
        name="b.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSNameConflictError):
        service.rename_item(
            user_id=user_id,
            item_id=a.item_id,
            new_name="b.txt",
        )


def test_move_file_ok(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )
    file_item = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    moved = service.move_item(
        user_id=user_id,
        item_id=file_item.item_id,
        parent_id=folder.item_id,
    )

    assert moved.parent_id == folder.item_id
    assert moved.item_id == file_item.item_id


def test_move_item_missing(service: VFSService, user_id: str) -> None:
    with pytest.raises(VFSItemNotFoundError):
        service.move_item(
            user_id=user_id,
            item_id="missing",
            parent_id=None,
        )


def test_move_parent_not_found(service: VFSService, user_id: str) -> None:
    file_item = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSParentNotFoundError):
        service.move_item(
            user_id=user_id,
            item_id=file_item.item_id,
            parent_id="missing-parent",
        )


def test_move_parent_is_file(service: VFSService, user_id: str) -> None:
    source = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )
    target_file = service.create_file_item(
        user_id=user_id,
        name="b.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSParentNotFolderError):
        service.move_item(
            user_id=user_id,
            item_id=source.item_id,
            parent_id=target_file.item_id,
        )


def test_move_folder_cycle_blocked(service: VFSService, user_id: str) -> None:
    root = service.create_folder(
        user_id=user_id,
        name="root",
        parent_id=None,
    )
    child = service.create_folder(
        user_id=user_id,
        name="child",
        parent_id=root.item_id,
    )

    with pytest.raises(VFSCycleError):
        service.move_item(
            user_id=user_id,
            item_id=root.item_id,
            parent_id=child.item_id,
        )


def test_move_folder_into_itself_blocked(service: VFSService, user_id: str) -> None:
    root = service.create_folder(
        user_id=user_id,
        name="root",
        parent_id=None,
    )

    with pytest.raises(VFSCycleError):
        service.move_item(
            user_id=user_id,
            item_id=root.item_id,
            parent_id=root.item_id,
        )


def test_move_item_name_conflict(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )
    service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=folder.item_id,
        size=1,
        mime="text/plain",
    )
    source = service.create_file_item(
        user_id=user_id,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    with pytest.raises(VFSNameConflictError):
        service.move_item(
            user_id=user_id,
            item_id=source.item_id,
            parent_id=folder.item_id,
        )


def test_repository_is_user_scoped(service: VFSService) -> None:
    a = service.create_folder(
        user_id="user-a",
        name="Docs",
        parent_id=None,
    )
    b = service.create_folder(
        user_id="user-b",
        name="Docs",
        parent_id=None,
    )

    assert a.item_id != b.item_id
    assert len(service.list_items("user-a")) == 1
    assert len(service.list_items("user-b")) == 1


def test_created_items_are_returned_from_repository(service: VFSService, user_id: str) -> None:
    folder = service.create_folder(
        user_id=user_id,
        name="Docs",
        parent_id=None,
    )
    fetched = service.get_item(
        user_id=user_id,
        item_id=folder.item_id,
    )

    assert fetched == folder