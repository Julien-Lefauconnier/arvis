# tests/kernel_core/vfs/test_vfs_syscalls.py

from __future__ import annotations

from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.vfs.models import VFSItem
from arvis.kernel_core.vfs.repositories.in_memory import InMemoryVFSRepository
from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.exceptions import ZipConflictError, ZipRejectedError
from arvis.kernel_core.vfs.zip.models import (
    ZipCollisionReport,
    ZipImportPlan,
    ZipImportPlanEntry,
    ZipNode,
)
from arvis.kernel_core.vfs.zip.service import ZipIngestDecision

# Important: import module so syscall decorators execute.
from arvis.kernel_core.syscalls.syscalls import vfs_syscalls  # noqa: F401


USER_ID = "user-1"


class StubZipIngestService:
    def __init__(self) -> None:
        self.last_execute_kwargs: dict | None = None
        self.planner = StubZipPlanner()
        self._decision = ZipIngestDecision(
            status="ready",
            zip_root=ZipNode(name="/", node_type="folder"),
        )
        self._execute_result = {
            "status": "completed",
            "imported_files": ["a.txt"],
            "skipped_files": [],
            "created_items": 1,
        }
        self._execute_exception: Exception | None = None

    def set_decision(self, decision: ZipIngestDecision) -> None:
        self._decision = decision

    def set_execute_result(self, result: dict) -> None:
        self._execute_result = result

    def set_execute_exception(self, exc: Exception | None) -> None:
        self._execute_exception = exc

    def analyze_and_validate(
        self,
        *,
        zip_path: str,
        user_id: str,
        target_parent_id: str | None,
    ) -> ZipIngestDecision:
        return self._decision

    def execute_from_path(
        self,
        *,
        zip_path: str,
        user_id: str,
        target_parent_id: str | None,
        keep_zip: bool = False,
        plan: ZipImportPlan | None = None,
    ) -> dict:
        self.last_execute_kwargs = {
            "zip_path": zip_path,
            "user_id": user_id,
            "target_parent_id": target_parent_id,
            "keep_zip": keep_zip,
            "plan": plan,
        }

        if self._execute_exception is not None:
            raise self._execute_exception

        return self._execute_result


class StubZipPlanner:
    def apply_plan(self, *, zip_root, plan):
        return zip_root


def _make_handler(
    *,
    vfs_service: VFSService | None = None,
    zip_ingest_service: StubZipIngestService | None = None,
) -> SyscallHandler:
    services = KernelServiceRegistry(
        vfs_service=vfs_service,
        zip_ingest_service=zip_ingest_service,
    )
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=services,
    )


def _find_item_by_name(service: VFSService, name: str) -> VFSItem:
    items = service.list_items(USER_ID)
    for item in items:
        if item.display_name == name:
            return item
    raise AssertionError(f"item not found in test setup: {name}")


# ============================================================
# VFS read syscalls
# ============================================================


def test_vfs_list_syscall_returns_serialized_items() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    service.create_folder(user_id=USER_ID, name="docs", parent_id=None)
    service.create_file_item(
        user_id=USER_ID,
        name="note.txt",
        parent_id=None,
        size=12,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.list",
            args={"user_id": USER_ID},
        )
    )

    assert result.success is True
    assert isinstance(result.result, list)
    assert len(result.result) == 2
    assert {item["display_name"] for item in result.result} == {"docs", "note.txt"}


def test_vfs_get_syscall_returns_serialized_item() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    created = service.create_folder(user_id=USER_ID, name="docs", parent_id=None)

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.get",
            args={
                "user_id": USER_ID,
                "item_id": created.item_id,
            },
        )
    )

    assert result.success is True
    assert result.result["item_id"] == created.item_id
    assert result.result["display_name"] == "docs"
    assert result.result["item_type"] == "folder"


def test_vfs_get_syscall_maps_not_found_error() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.get",
            args={
                "user_id": USER_ID,
                "item_id": "missing",
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_item_not_found"


def test_vfs_tree_syscall_returns_serialized_tree() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    folder = service.create_folder(user_id=USER_ID, name="docs", parent_id=None)
    service.create_file_item(
        user_id=USER_ID,
        name="a.txt",
        parent_id=folder.item_id,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.tree",
            args={"user_id": USER_ID},
        )
    )

    assert result.success is True
    assert isinstance(result.result, list)
    assert len(result.result) == 1
    root = result.result[0]
    assert root["item"]["display_name"] == "docs"
    assert len(root["children"]) == 1
    assert root["children"][0]["item"]["display_name"] == "a.txt"


def test_vfs_list_syscall_fails_without_service() -> None:
    handler = _make_handler()

    result = handler.handle(
        Syscall(
            name="vfs.list",
            args={"user_id": USER_ID},
        )
    )

    assert result.success is False
    assert result.error == "no_vfs_service"


# ============================================================
# VFS write syscalls
# ============================================================


def test_vfs_create_folder_syscall_creates_folder() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.create_folder",
            args={
                "user_id": USER_ID,
                "name": "docs",
                "parent_id": None,
            },
        )
    )

    assert result.success is True
    assert result.result["display_name"] == "docs"
    assert result.result["item_type"] == "folder"


def test_vfs_create_folder_syscall_maps_invalid_name() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.create_folder",
            args={
                "user_id": USER_ID,
                "name": "   ",
                "parent_id": None,
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_invalid_name"


def test_vfs_create_folder_syscall_maps_parent_not_found() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.create_folder",
            args={
                "user_id": USER_ID,
                "name": "docs",
                "parent_id": "missing-parent",
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_parent_not_found"


def test_vfs_create_file_syscall_creates_file() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.create_file",
            args={
                "user_id": USER_ID,
                "name": "note.txt",
                "parent_id": None,
                "size": 10,
                "mime": "text/plain",
            },
        )
    )

    assert result.success is True
    assert result.result["display_name"] == "note.txt"
    assert result.result["item_type"] == "file"
    assert result.result["mime"] == "text/plain"


def test_vfs_create_file_syscall_maps_name_conflict() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    service.create_file_item(
        user_id=USER_ID,
        name="note.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.create_file",
            args={
                "user_id": USER_ID,
                "name": "note.txt",
                "parent_id": None,
                "size": 2,
                "mime": "text/plain",
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_name_conflict"


def test_vfs_delete_item_syscall_deletes_file() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    item = service.create_file_item(
        user_id=USER_ID,
        name="note.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.delete_item",
            args={
                "user_id": USER_ID,
                "item_id": item.item_id,
            },
        )
    )

    assert result.success is True
    assert result.result == {"deleted": True, "item_id": item.item_id}
    assert service.list_items(USER_ID) == []


def test_vfs_delete_item_syscall_maps_folder_not_empty() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    folder = service.create_folder(user_id=USER_ID, name="docs", parent_id=None)
    service.create_file_item(
        user_id=USER_ID,
        name="a.txt",
        parent_id=folder.item_id,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.delete_item",
            args={
                "user_id": USER_ID,
                "item_id": folder.item_id,
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_folder_not_empty"


def test_vfs_rename_item_syscall_renames_item() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    item = service.create_file_item(
        user_id=USER_ID,
        name="old.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.rename_item",
            args={
                "user_id": USER_ID,
                "item_id": item.item_id,
                "new_name": "new.txt",
            },
        )
    )

    assert result.success is True
    assert result.result["display_name"] == "new.txt"


def test_vfs_rename_item_syscall_maps_conflict() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    item_a = service.create_file_item(
        user_id=USER_ID,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )
    service.create_file_item(
        user_id=USER_ID,
        name="b.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.rename_item",
            args={
                "user_id": USER_ID,
                "item_id": item_a.item_id,
                "new_name": "b.txt",
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_name_conflict"


def test_vfs_move_item_syscall_moves_item() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    folder = service.create_folder(user_id=USER_ID, name="docs", parent_id=None)
    item = service.create_file_item(
        user_id=USER_ID,
        name="note.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.move_item",
            args={
                "user_id": USER_ID,
                "item_id": item.item_id,
                "parent_id": folder.item_id,
            },
        )
    )

    assert result.success is True
    assert result.result["parent_id"] == folder.item_id


def test_vfs_move_item_syscall_maps_parent_not_folder() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    target = service.create_file_item(
        user_id=USER_ID,
        name="not-a-folder.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )
    item = service.create_file_item(
        user_id=USER_ID,
        name="note.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.move_item",
            args={
                "user_id": USER_ID,
                "item_id": item.item_id,
                "parent_id": target.item_id,
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_parent_not_folder"


def test_vfs_move_item_syscall_maps_cycle_error() -> None:
    repo = InMemoryVFSRepository()
    service = VFSService(repo)
    root = service.create_folder(user_id=USER_ID, name="root", parent_id=None)
    child = service.create_folder(user_id=USER_ID, name="child", parent_id=root.item_id)

    handler = _make_handler(vfs_service=service)

    result = handler.handle(
        Syscall(
            name="vfs.move_item",
            args={
                "user_id": USER_ID,
                "item_id": root.item_id,
                "parent_id": child.item_id,
            },
        )
    )

    assert result.success is False
    assert result.error == "vfs_cycle_error"


# ============================================================
# ZIP syscalls
# ============================================================


def test_vfs_zip_analyze_syscall_returns_serialized_decision_ready() -> None:
    zip_service = StubZipIngestService()
    zip_service.set_decision(
        ZipIngestDecision(
            status="ready",
            zip_root=ZipNode(
                name="/",
                node_type="folder",
                children=[
                    ZipNode(
                        name="docs",
                        node_type="folder",
                        children=[
                            ZipNode(
                                name="a.txt",
                                node_type="file",
                                zip_path="docs/a.txt",
                                size=10,
                                extension=".txt",
                                supported=True,
                            )
                        ],
                    )
                ],
            ),
        )
    )

    handler = _make_handler(zip_ingest_service=zip_service)

    result = handler.handle(
        Syscall(
            name="vfs.zip.analyze",
            args={
                "zip_path": "/tmp/test.zip",
                "user_id": USER_ID,
                "target_parent_id": None,
            },
        )
    )

    assert result.success is True
    assert result.result["status"] == "ready"
    assert result.result["zip_root"]["name"] == "/"
    assert result.result["zip_root"]["children"][0]["name"] == "docs"


def test_vfs_zip_analyze_syscall_returns_serialized_conflicts() -> None:
    repo = InMemoryVFSRepository()
    vfs_service = VFSService(repo)
    existing = vfs_service.create_file_item(
        user_id=USER_ID,
        name="a.txt",
        parent_id=None,
        size=1,
        mime="text/plain",
    )

    zip_service = StubZipIngestService()
    zip_service.set_decision(
        ZipIngestDecision(
            status="conflict",
            zip_root=ZipNode(name="/", node_type="folder"),
            collisions=ZipCollisionReport(
                has_conflicts=True,
                collisions=[
                    vfs_syscalls.ZipCollision(
                        zip_node=ZipNode(
                            name="a.txt",
                            node_type="file",
                            zip_path="a.txt",
                            supported=True,
                        ),
                        vfs_item=existing,
                        reason="already_exists",
                    )
                ],
            ),
        )
    )

    handler = _make_handler(
        vfs_service=vfs_service,
        zip_ingest_service=zip_service,
    )

    result = handler.handle(
        Syscall(
            name="vfs.zip.analyze",
            args={
                "zip_path": "/tmp/test.zip",
                "user_id": USER_ID,
                "target_parent_id": None,
            },
        )
    )

    assert result.success is True
    assert result.result["status"] == "conflict"
    assert result.result["collisions"]["has_conflicts"] is True
    assert len(result.result["collisions"]["collisions"]) == 1
    collision = result.result["collisions"]["collisions"][0]
    assert collision["reason"] == "already_exists"
    assert collision["vfs_item"]["display_name"] == "a.txt"


def test_vfs_zip_execute_syscall_executes_successfully() -> None:
    zip_service = StubZipIngestService()
    handler = _make_handler(zip_ingest_service=zip_service)

    plan = ZipImportPlan(
        entries={
            "docs/a.txt": ZipImportPlanEntry(action="rename", new_name="renamed.txt"),
        }
    )

    result = handler.handle(
        Syscall(
            name="vfs.zip.execute",
            args={
                "zip_path": "/tmp/test.zip",
                "user_id": USER_ID,
                "target_parent_id": "folder-1",
                "keep_zip": True,
                "plan": plan,
            },
        )
    )

    assert result.success is True
    assert result.result["status"] == "completed"
    assert zip_service.last_execute_kwargs is not None
    assert zip_service.last_execute_kwargs["zip_path"] == "/tmp/test.zip"
    assert zip_service.last_execute_kwargs["user_id"] == USER_ID
    assert zip_service.last_execute_kwargs["target_parent_id"] == "folder-1"
    assert zip_service.last_execute_kwargs["keep_zip"] is True
    assert zip_service.last_execute_kwargs["plan"] == plan


def test_vfs_zip_execute_syscall_maps_rejected_error() -> None:
    zip_service = StubZipIngestService()
    zip_service.set_execute_exception(ZipRejectedError("bad zip"))

    handler = _make_handler(zip_ingest_service=zip_service)

    result = handler.handle(
        Syscall(
            name="vfs.zip.execute",
            args={
                "zip_path": "/tmp/test.zip",
                "user_id": USER_ID,
            },
        )
    )

    assert result.success is False
    assert result.error == "zip_rejected"


def test_vfs_zip_execute_syscall_maps_conflict_error() -> None:
    zip_service = StubZipIngestService()
    zip_service.set_execute_exception(ZipConflictError("conflict"))

    handler = _make_handler(zip_ingest_service=zip_service)

    result = handler.handle(
        Syscall(
            name="vfs.zip.execute",
            args={
                "zip_path": "/tmp/test.zip",
                "user_id": USER_ID,
            },
        )
    )

    assert result.success is False
    assert result.error == "zip_conflict"


def test_vfs_zip_execute_syscall_fails_without_service() -> None:
    handler = _make_handler()

    result = handler.handle(
        Syscall(
            name="vfs.zip.execute",
            args={
                "zip_path": "/tmp/test.zip",
                "user_id": USER_ID,
            },
        )
    )

    assert result.success is False
    assert result.error == "no_zip_ingest_service"


def test_vfs_zip_plan_basic():
    zip_service = StubZipIngestService()
    handler = _make_handler(zip_ingest_service=zip_service)

    analyze = handler.handle(
        Syscall(
            name="vfs.zip.analyze",
            args={
                "zip_path": "test.zip",
                "user_id": "u1",
            },
        )
    )

    root = analyze.result["zip_root"]

    plan = {
        "entries": [
            {
                "zip_path": "file.txt",
                "action": "rename",
                "new_name": "renamed.txt",
            }
        ]
    }

    res = handler.handle(
        Syscall(
            name="vfs.zip.plan",
            args={
                "zip_root": root,
                "plan": plan,
            },
        )
    )

    assert res.success
    assert res.result is not None
