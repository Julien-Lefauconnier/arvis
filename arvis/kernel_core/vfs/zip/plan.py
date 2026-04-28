# arvis/kernel_core/vsf/zip/plan.py

from __future__ import annotations

from arvis.kernel_core.vfs.zip.models import ZipImportPlan, ZipNode


class ZipImportPlanError(ValueError):
    """Raised when a ZIP import plan is invalid."""


class ZipImportPlanService:
    """
    Apply a user-defined import plan to a ZipNode tree.

    This operates only on the ZIP logical structure and has
    no dependency on persistence or VFS state.
    """

    def apply_plan(
        self,
        *,
        zip_root: ZipNode,
        plan: ZipImportPlan,
    ) -> ZipNode:
        if not plan.entries:
            return zip_root

        seen_targets: set[str] = set()

        def walk(node: ZipNode) -> bool:
            if node.is_file():
                if node.zip_path is None:
                    raise ZipImportPlanError("file node missing zip_path")

                entry = plan.entries.get(node.zip_path)
                if entry is None:
                    return True

                if entry.action == "skip":
                    return False

                if entry.action == "rename":
                    if not entry.new_name:
                        raise ZipImportPlanError(
                            f"missing new_name for rename: {node.zip_path}"
                        )

                    if "/" in entry.new_name or "\\" in entry.new_name:
                        raise ZipImportPlanError("invalid rename target")

                    if entry.new_name in seen_targets:
                        raise ZipImportPlanError(
                            f"duplicate rename target: {entry.new_name}"
                        )

                    node.name = entry.new_name
                    seen_targets.add(entry.new_name)

            kept_children: list[ZipNode] = []
            for child in node.children:
                if walk(child):
                    kept_children.append(child)

            node.children = kept_children
            return True

        walk(zip_root)
        return zip_root
