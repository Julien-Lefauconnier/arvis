# arvis/kernel/pipeline/context/projection_context.py

from dataclasses import dataclass

from arvis.cognition.projection.projection_result import ProjectionResult
from arvis.kernel.projection.certificate import ProjectionCertificate
from arvis.kernel.projection.projected_state import ProjectedState


@dataclass
class PipelineProjectionContext:
    certificate: ProjectionCertificate | None = None
    domain_valid: bool | None = None
    margin: float | None = None

    # Post-hoc attestation (campaign PROJ, DM-P2): the decision view
    # re-validated during finalize against signals that only exist
    # after the gate, the composite energy delta first of all. The
    # decision fields above are what the gate consumed and are never
    # rewritten; this one says what is known after the fact.
    post_certificate: ProjectionCertificate | None = None

    # -----------------------------------------------------
    # Canonical projection namespaces
    # -----------------------------------------------------
    # runtime_projection:
    #   Deterministic runtime Π_impl extraction used by
    #   certification and gate evaluation.
    #
    # structured_projection:
    #   Structured theoretical/intermediate Π projection
    #   preserving semantic decomposition (x, z, q, w).
    # -----------------------------------------------------
    runtime_projection: ProjectedState | None = None
    structured_projection: ProjectionResult | None = None

    view: dict[str, float] | None = None
    view_raw: dict[str, float] | None = None
