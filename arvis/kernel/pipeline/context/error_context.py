# arvis/kernel/pipeline/context/error_context.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.errors.base import ArvisError


@dataclass
class PipelineErrorContext:
    """
    Canonical runtime error domain.

    Responsibilities:
    - runtime error accumulation
    - degraded-mode tracking
    - replay-safe error projections
    - deterministic error ownership

    No IO.
    No logging backend.
    No infra.
    """

    errors: list[ArvisError] = field(default_factory=list)

    degraded_mode: bool = False

    fatal_error: ArvisError | None = None
