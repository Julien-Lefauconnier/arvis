# tests/kernel_core/vfs/test_zip_plan.py

from __future__ import annotations

import pytest

from arvis.kernel_core.vfs.zip.models import (
    ZipImportPlan,
    ZipImportPlanEntry,
    ZipNode,
)
from arvis.kernel_core.vfs.zip.plan import ZipImportPlanError, ZipImportPlanService


def test_zip_plan_skip_file() -> None:
    root = ZipNode(name="/", node_type="folder")
    file_node = ZipNode(name="a.txt", node_type="file", zip_path="a.txt")
    root.add_child(file_node)

    plan = ZipImportPlan(
        entries={
            "a.txt": ZipImportPlanEntry(action="skip"),
        }
    )

    service = ZipImportPlanService()
    updated = service.apply_plan(zip_root=root, plan=plan)

    assert updated.children == []


def test_zip_plan_rename_file() -> None:
    root = ZipNode(name="/", node_type="folder")
    file_node = ZipNode(name="a.txt", node_type="file", zip_path="a.txt")
    root.add_child(file_node)

    plan = ZipImportPlan(
        entries={
            "a.txt": ZipImportPlanEntry(action="rename", new_name="renamed.txt"),
        }
    )

    service = ZipImportPlanService()
    updated = service.apply_plan(zip_root=root, plan=plan)

    assert updated.children[0].name == "renamed.txt"


def test_zip_plan_rejects_missing_new_name() -> None:
    root = ZipNode(name="/", node_type="folder")
    file_node = ZipNode(name="a.txt", node_type="file", zip_path="a.txt")
    root.add_child(file_node)

    plan = ZipImportPlan(
        entries={
            "a.txt": ZipImportPlanEntry(action="rename", new_name=None),
        }
    )

    service = ZipImportPlanService()

    with pytest.raises(ZipImportPlanError):
        service.apply_plan(zip_root=root, plan=plan)


def test_zip_plan_rejects_invalid_rename_target() -> None:
    root = ZipNode(name="/", node_type="folder")
    file_node = ZipNode(name="a.txt", node_type="file", zip_path="a.txt")
    root.add_child(file_node)

    plan = ZipImportPlan(
        entries={
            "a.txt": ZipImportPlanEntry(action="rename", new_name="bad/name.txt"),
        }
    )

    service = ZipImportPlanService()

    with pytest.raises(ZipImportPlanError):
        service.apply_plan(zip_root=root, plan=plan)