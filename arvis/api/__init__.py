# arvis/api/_init__.py
"""
Public API surface for ARVIS Cognitive OS.
"""

# -----------------------------------------------------
# Core OS
# -----------------------------------------------------
from .os import CognitiveOS, CognitiveResultView, CognitiveOSConfig
from .trace import DecisionTraceView
from .timeline import TimelineView
from .version import API_VERSION, API_FINGERPRINT


# -----------------------------------------------------
# Explicit Public Contracts (STANDARD)
# -----------------------------------------------------

# cognition
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.policy.cognitive_policy_result import CognitivePolicyResult
from arvis.cognition.policy.cognitive_signal_snapshot import CognitiveSignalSnapshot

# memory
from arvis.memory.memory_intent import MemoryIntent
from arvis.memory.memory_gate import MemoryGate
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot
from arvis.memory.memory_long_entry import MemoryLongType

# reasoning
from arvis.reasoning.reasoning_intent import (
    ReasoningIntent,
    ReasoningIntentType,
)

# uncertainty
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame
from arvis.uncertainty.uncertainty_frame_registry import UncertaintyFrameRegistry

# math / lyapunov
from arvis.math.lyapunov.lyapunov import (
    LyapunovState,
    LyapunovWeights,
    lyapunov_value,
    lyapunov_delta,
)

# math utils
from arvis.math.core.normalization import (
    clamp,
    clamp01,
    normalize_weights,
)

# risk
from arvis.math.risk.risk_bound import (
    HoeffdingRiskBound,
    RiskBoundSnapshot,
)

# control
from arvis.control.control_inertia import ControlInertia

# stability
from arvis.stability.stability_observer import StabilityObserver
from arvis.stability.stability_snapshot import StabilitySnapshot
from arvis.api.stability import StabilityView


# IR
from .ir import build_ir_view
from .ir_canonical import canonicalize_ir, hash_ir

# -----------------------------------------------------
# PUBLIC SURFACE (CONTRACT)
# -----------------------------------------------------
__all__ = [
    # OS
    "CognitiveOS",
    "CognitiveResultView",
    "CognitiveOSConfig",

    # Views (API layer)
    "DecisionTraceView",
    "TimelineView",
    "StabilityView",

    # Versioning
    "API_VERSION",
    "API_FINGERPRINT",

    # Cognition
    "CognitiveBundleBuilder",
    "CognitiveBundleSnapshot",
    "CognitiveState",
    "ChangeBudget",
    "CognitivePolicyResult",
    "CognitiveSignalSnapshot",

    # Memory
    "MemoryIntent",
    "MemoryGate",
    "MemoryLongSnapshot",
    "MemoryLongType",

    # Reasoning
    "ReasoningIntent",
    "ReasoningIntentType",

    # Uncertainty
    "UncertaintyAxis",
    "UncertaintyFrame",
    "UncertaintyFrameRegistry",

    # Math / Lyapunov
    "LyapunovState",
    "LyapunovWeights",
    "lyapunov_value",
    "lyapunov_delta",

    # Math utils
    "clamp",
    "clamp01",
    "normalize_weights",

    # Risk
    "HoeffdingRiskBound",
    "RiskBoundSnapshot",

    # Control
    "ControlInertia",

    # Stability
    "StabilityObserver",
    "StabilitySnapshot",

    # IR (new public layer)
    "build_ir_view",
    "canonicalize_ir",
    "hash_ir",
]