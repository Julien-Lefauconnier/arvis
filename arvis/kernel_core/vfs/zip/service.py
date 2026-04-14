# arvis/kernel_core/vfs/zip/service.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from arvis.kernel_core.vfs.service import VFSService
from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer
from arvis.kernel_core.vfs.zip.collision import ZipCollisionService
from arvis.kernel_core.vfs.zip.executor import ZipExecutor
from arvis.kernel_core.vfs.zip.exceptions import (
    ZipConflictError,
    ZipRejectedError,
)
from arvis.kernel_core.vfs.zip.models import (
    ZipCollisionReport,
    ZipImportPlan,
    ZipNode,
)
from arvis.kernel_core.vfs.zip.plan import ZipImportPlanService


@dataclass(frozen=True)
class ZipIngestDecision:
    """
    Structured decision produced by the ZIP dry-run phase.
    """

    status: str  # "ready" | "conflict" | "rejected"
    zip_root: Optional[ZipNode] = None
    collisions: Optional[ZipCollisionReport] = None
    reason: Optional[str] = None


class ZipIngestService:
    """
    ZIP orchestration service in a VFS-first architecture.

    Strict separation:
    - phase 1: analyze + collision detection (dry-run)
    - phase 2: actual execution (after validation)
    """

    def __init__(
        self,
        *,
        analyzer: ZipAnalyzer,
        collision_service: ZipCollisionService,
        executor: ZipExecutor,
        planner: ZipImportPlanService,
        vfs_service: VFSService,
    ) -> None:
        self.analyzer = analyzer
        self.collision_service = collision_service
        self.executor = executor
        self.planner = planner
        self.vfs = vfs_service

    def analyze_and_validate(
        self,
        *,
        zip_path: str,
        user_id: str,
        target_parent_id: Optional[str],
    ) -> ZipIngestDecision:
        try:
            zip_root = self.analyzer.analyze(zip_path)

            collisions = self.collision_service.detect(
                zip_root=zip_root,
                user_id=user_id,
                target_parent_id=target_parent_id,
            )

            if collisions.has_conflicts:
                return ZipIngestDecision(
                    status="conflict",
                    zip_root=zip_root,
                    collisions=collisions,
                )

            return ZipIngestDecision(
                status="ready",
                zip_root=zip_root,
            )

        except Exception as exc:
            return ZipIngestDecision(
                status="rejected",
                reason=str(exc),
            )

    def execute_import(
        self,
        *,
        zip_root: ZipNode,
        zip_path: str,
        user_id: str,
        target_parent_id: Optional[str],
        keep_zip: bool = False,
        plan: Optional[ZipImportPlan] = None,
    ) -> dict[str, object]:
        if plan is not None:
            zip_root = self.planner.apply_plan(
                zip_root=zip_root,
                plan=plan,
            )

        return self.executor.execute(
            zip_root=zip_root,
            zip_path=zip_path,
            user_id=user_id,
            target_parent_id=target_parent_id,
            keep_zip=keep_zip,
        )

    def execute_from_path(
        self,
        *,
        zip_path: str,
        user_id: str,
        target_parent_id: Optional[str],
        keep_zip: bool = False,
        plan: Optional[ZipImportPlan] = None,
    ) -> dict[str, object]:
        decision = self.analyze_and_validate(
            zip_path=zip_path,
            user_id=user_id,
            target_parent_id=target_parent_id,
        )

        if decision.status == "rejected":
            raise ZipRejectedError(decision.reason or "zip analysis rejected")

        if decision.status == "conflict":
            raise ZipConflictError("zip conflicts detected")

        if decision.zip_root is None:
            raise ZipRejectedError("zip analysis produced no executable root")

        return self.execute_import(
            zip_root=decision.zip_root,
            zip_path=zip_path,
            user_id=user_id,
            target_parent_id=target_parent_id,
            keep_zip=keep_zip,
            plan=plan,
        )