# arvis/kernel/pipeline/services/pipeline_ir_service.py

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

from arvis.adapters.ir.projection_adapter import ProjectionIRAdapter
from arvis.adapters.ir.validity_adapter import ValidityIRAdapter
from arvis.adapters.ir.stability_adapter import StabilityIRAdapter
from arvis.adapters.ir.adaptive_adapter import AdaptiveIRAdapter
from arvis.adapters.ir.cognitive_ir_builder import CognitiveIRBuilder

from arvis.ir.normalization.cognitive_ir_normalizer import (
    CognitiveIRNormalizer,
)
from arvis.ir.validation.cognitive_ir_validator import (
    CognitiveIRValidator,
)
from arvis.ir.serialization.cognitive_ir_serializer import (
    CognitiveIRSerializer,
)
from arvis.ir.serialization.cognitive_ir_hasher import (
    CognitiveIRHasher,
)
from arvis.ir.envelope import CognitiveIREnvelope


class PipelineIRService:
    @staticmethod
    def run(ctx: CognitivePipelineContext) -> None:
        # -----------------------------------------
        # Projection IR
        # -----------------------------------------
        try:
            ctx.ir_projection = ProjectionIRAdapter.from_projection(
                getattr(ctx, "projection_certificate", None)
            )
        except Exception:
            ctx.ir_projection = None
            ctx.extra.setdefault("errors", []).append(
                "projection_ir_adapter_failure"
            )

        # -----------------------------------------
        # Validity IR
        # -----------------------------------------
        try:
            ctx.ir_validity = ValidityIRAdapter.from_validity(
                getattr(ctx, "validity_envelope", None)
            )
        except Exception:
            ctx.ir_validity = None
            ctx.extra.setdefault("errors", []).append(
                "validity_ir_adapter_failure"
            )

        # -----------------------------------------
        # Stability IR
        # -----------------------------------------
        try:
            ctx.ir_stability = StabilityIRAdapter.from_stability(
                getattr(ctx, "stability_projection", None)
            )
        except Exception:
            ctx.ir_stability = None
            ctx.extra.setdefault("errors", []).append(
                "stability_ir_adapter_failure"
            )

        # -----------------------------------------
        # Adaptive IR
        # -----------------------------------------
        try:
            ctx.ir_adaptive = AdaptiveIRAdapter.from_adaptive(
                getattr(ctx, "adaptive_snapshot", None)
            )
        except Exception:
            ctx.ir_adaptive = None
            ctx.extra.setdefault("errors", []).append(
                "adaptive_ir_adapter_failure"
            )

        # -----------------------------------------
        # Build canonical IR
        # -----------------------------------------
        try:
            ctx.cognitive_ir = CognitiveIRBuilder.from_context(ctx)
        except Exception:
            ctx.cognitive_ir = None
            ctx.extra.setdefault("errors", []).append(
                "cognitive_ir_build_failure"
            )
            return

        # -----------------------------------------
        # Normalize
        # -----------------------------------------
        ctx.cognitive_ir = CognitiveIRNormalizer.normalize(
            ctx.cognitive_ir
        )

        # -----------------------------------------
        # Validate
        # -----------------------------------------
        try:
            CognitiveIRValidator.validate(ctx.cognitive_ir)
        except Exception:
            ctx.extra.setdefault("errors", []).append(
                "cognitive_ir_validation_failure"
            )
            raise

        # -----------------------------------------
        # Serialize / hash / envelope
        # -----------------------------------------
        try:
            ctx.ir_serialized = (
                CognitiveIRSerializer.to_canonical_dict(
                    ctx.cognitive_ir
                )
            )

            ctx.ir_hash = CognitiveIRHasher.hash(
                ctx.cognitive_ir
            )

            ctx.ir_envelope = CognitiveIREnvelope.build(
                ir=ctx.cognitive_ir,
                serialized=ctx.ir_serialized,
                hash_value=ctx.ir_hash,
            )

        except Exception:
            ctx.ir_serialized = None
            ctx.ir_hash = None
            ctx.ir_envelope = None

            ctx.extra.setdefault("errors", []).append(
                "ir_serialization_failure"
            )