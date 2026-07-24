# arvis/__init__.py
"""
Top-level public API.

Only stable high-level entrypoints are exposed here.
"""

from .api.audit import AuditCommitmentPolicy
from .api.contracts.result_schema import (
    RESULT_SCHEMA_VERSION,
    load_result_schema,
)
from .api.engine import ArvisEngine
from .api.os import CognitiveOS, CognitiveOSConfig
from .api.reflexive import verify_reflexive_attestation
from .api.runtime_controls import TrustedRuntimeControls
from .api.runtime_mode import RuntimeMode
from .api.version import PACKAGE_VERSION
from .api.views.cognitive_result_view import CognitiveResultView
from .api.views.decision_status import DecisionStatus

__version__ = PACKAGE_VERSION

__all__ = [
    "RESULT_SCHEMA_VERSION",
    "ArvisEngine",
    "AuditCommitmentPolicy",
    "CognitiveOS",
    "CognitiveOSConfig",
    "CognitiveResultView",
    "DecisionStatus",
    "RuntimeMode",
    "TrustedRuntimeControls",
    "load_result_schema",
    "verify_reflexive_attestation",
]
