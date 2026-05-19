# arvis/kernel/pipeline/context/observability_context.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.kernel.pipeline.context.observability.diagnostic_context import (
    ObservabilityDiagnosticContext,
)
from arvis.kernel.pipeline.context.observability.projections_context import (
    ObservabilityProjectionContext,
)
from arvis.kernel.pipeline.context.observability.state_context import (
    ObservabilityStateContext,
)
from arvis.kernel.pipeline.context.observability.symbolic_context import (
    ObservabilitySymbolicContext,
)


@dataclass
class PipelineObservabilityContext:
    """
    Canonical observability bounded context.

    Responsibilities:
    - projections
    - symbolic observability
    - diagnostics
    - replay-safe state exposure
    """

    projections: ObservabilityProjectionContext = field(
        default_factory=ObservabilityProjectionContext,
    )

    symbolic: ObservabilitySymbolicContext = field(
        default_factory=ObservabilitySymbolicContext,
    )

    state: ObservabilityStateContext = field(
        default_factory=ObservabilityStateContext,
    )

    diagnostics: ObservabilityDiagnosticContext = field(
        default_factory=ObservabilityDiagnosticContext,
    )
