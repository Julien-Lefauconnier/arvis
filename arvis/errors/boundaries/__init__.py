# arvis/errors/boundaries/__init__.py

from arvis.errors.boundaries.observability import (
    capture_observability_failure,
)
from arvis.errors.boundaries.pipeline import (
    capture_pipeline_degraded_failure,
)

__all__ = [
    "capture_observability_failure",
    "capture_pipeline_degraded_failure",
]
