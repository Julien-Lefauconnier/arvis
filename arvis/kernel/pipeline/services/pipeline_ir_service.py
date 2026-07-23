# arvis/kernel/pipeline/services/pipeline_ir_service.py

from __future__ import annotations

import json
from typing import Any, cast

from arvis.adapters.ir.adaptive_adapter import AdaptiveIRAdapter
from arvis.adapters.ir.cognitive_ir_builder import CognitiveIRBuilder
from arvis.adapters.ir.projection_adapter import ProjectionIRAdapter
from arvis.adapters.ir.stability_adapter import StabilityIRAdapter
from arvis.adapters.ir.validity_adapter import ValidityIRAdapter
from arvis.errors.boundaries.pipeline import (
    capture_pipeline_contract_failure,
    capture_pipeline_degraded_failure,
)
from arvis.ir.envelope import CognitiveIREnvelope
from arvis.ir.normalization.cognitive_ir_normalizer import (
    CognitiveIRNormalizer,
)
from arvis.ir.serialization.cognitive_ir_hasher import (
    CognitiveIRHasher,
)
from arvis.ir.serialization.cognitive_ir_serializer import (
    CognitiveIRSerializer,
)
from arvis.ir.validation.cognitive_ir_validator import (
    CognitiveIRValidator,
)
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


class PipelineIRService:
    @staticmethod
    def run(ctx: CognitivePipelineContext) -> None:
        # -----------------------------------------
        # Projection IR
        # -----------------------------------------
        try:
            ctx.ir_projection = ProjectionIRAdapter.from_projection(
                ctx.projection.certificate
            )
        except Exception as exc:
            ctx.ir_projection = None
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="ProjectionIRAdapter",
                message="Projection IR adapter failure",
            )

        # -----------------------------------------
        # Validity IR
        # -----------------------------------------
        try:
            ctx.ir_validity = ValidityIRAdapter.from_validity(
                getattr(ctx, "validity_envelope", None)
            )
        except Exception as exc:
            ctx.ir_validity = None
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="ValidityIRAdapter",
                message="Validity IR adapter failure",
            )

        # -----------------------------------------
        # Stability IR
        # -----------------------------------------
        try:
            ctx.ir_stability = StabilityIRAdapter.from_stability(
                getattr(ctx, "stability_projection", None)
            )
        except Exception as exc:
            ctx.ir_stability = None
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="StabilityIRAdapter",
                message="Stability IR adapter failure",
            )

        # -----------------------------------------
        # Adaptive IR
        # -----------------------------------------
        try:
            ctx.ir_adaptive = AdaptiveIRAdapter.from_adaptive(
                getattr(ctx, "adaptive_snapshot", None)
            )
        except Exception as exc:
            ctx.ir_adaptive = None
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="AdaptiveIRAdapter",
                message="Adaptive IR adapter failure",
            )

        # -----------------------------------------
        # Build canonical IR
        # -----------------------------------------
        try:
            ctx.cognitive_ir = CognitiveIRBuilder.from_context(ctx)
        except Exception as exc:
            ctx.cognitive_ir = None
            capture_pipeline_degraded_failure(
                ctx,
                exc,
                component="CognitiveIRBuilder",
                message="Cognitive IR build failure",
            )
            return

        # -----------------------------------------
        # Normalize
        # -----------------------------------------
        ctx.cognitive_ir = CognitiveIRNormalizer.normalize(ctx.cognitive_ir)

        # -----------------------------------------
        # Validate
        # -----------------------------------------
        try:
            CognitiveIRValidator.validate(ctx.cognitive_ir)
        except Exception as exc:
            capture_pipeline_contract_failure(
                ctx,
                exc,
                component="CognitiveIRValidator",
                message="Cognitive IR validation failure",
            )
            raise

        # -----------------------------------------
        # Serialize / hash / envelope
        # -----------------------------------------
        # P1-04 (audit a13): one canonical serialization. The witness
        # dict, the hash and the envelope all derive from the same
        # canonical text, so a mutation of the live IR between steps can
        # no longer desynchronize the exported witness from its hash.
        try:
            canonical_text = CognitiveIRSerializer.serialize(ctx.cognitive_ir)
            loaded = json.loads(canonical_text)
            if not isinstance(loaded, dict):
                raise TypeError("Canonical IR must be a dict")
            ctx.ir_serialized = cast(dict[str, Any], loaded)

            ctx.ir_hash = CognitiveIRHasher.hash_canonical_text(canonical_text)

            ctx.ir_envelope = CognitiveIREnvelope.build(
                ir=ctx.cognitive_ir,
                serialized=ctx.ir_serialized,
                hash_value=ctx.ir_hash,
            )

        except Exception as exc:
            ctx.ir_serialized = None
            ctx.ir_hash = None
            ctx.ir_envelope = None

            capture_pipeline_contract_failure(
                ctx,
                exc,
                component="CognitiveIRSerialization",
                message="IR serialization failure",
            )
            raise
