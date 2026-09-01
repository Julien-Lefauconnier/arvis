# tests/kernel/pipeline/services/test_pipeline_ir_service_failures.py
"""IR service failure semantics: degrade per axis, fail closed on core.

Campaign RELEASE (LOT R2). The per-axis IR adapters degrade to None
with a captured degraded error (the run continues); the validator and
the canonical serializer are contract boundaries: their failures are
captured as contract violations and RAISED, and a serialization
failure nulls all three derived artifacts (witness, hash, envelope)
so nothing half-serialized escapes.
"""

from __future__ import annotations

import pytest

from arvis.kernel.pipeline.services import pipeline_ir_service as ir_service_module
from arvis.kernel.pipeline.services.pipeline_ir_service import PipelineIRService
from tests.fixtures.builders.context_builder import (
    build_finalize_compatible_context,
)


def test_projection_adapter_failure_degrades_to_none(monkeypatch) -> None:
    ctx = build_finalize_compatible_context()

    def _boom(certificate):
        raise RuntimeError("adapter down")

    monkeypatch.setattr(
        ir_service_module.ProjectionIRAdapter, "from_projection", staticmethod(_boom)
    )

    PipelineIRService.run(ctx)

    assert ctx.ir_projection is None
    assert any(
        getattr(e, "details", {}).get("component") == "ProjectionIRAdapter"
        for e in ctx.error_state.errors
    )
    # the core IR artifacts still exist: the axis degraded, the run held
    assert ctx.ir_hash is not None
    assert ctx.ir_envelope is not None


def test_validator_failure_is_a_raised_contract_violation(monkeypatch) -> None:
    ctx = build_finalize_compatible_context()

    def _boom(ir):
        raise ValueError("inconsistent IR")

    monkeypatch.setattr(
        ir_service_module.CognitiveIRValidator, "validate", staticmethod(_boom)
    )

    with pytest.raises(ValueError):
        PipelineIRService.run(ctx)

    assert any(
        getattr(e, "details", {}).get("component") == "CognitiveIRValidator"
        for e in ctx.error_state.errors
    )


def test_serializer_failure_nulls_every_derived_artifact(monkeypatch) -> None:
    ctx = build_finalize_compatible_context()

    def _boom(ir):
        raise RuntimeError("serializer down")

    monkeypatch.setattr(
        ir_service_module.CognitiveIRSerializer, "serialize", staticmethod(_boom)
    )

    with pytest.raises(RuntimeError):
        PipelineIRService.run(ctx)

    assert ctx.ir_serialized is None
    assert ctx.ir_hash is None
    assert ctx.ir_envelope is None
