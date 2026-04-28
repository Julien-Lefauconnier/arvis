# arvis/api/__init__.py
"""
Public API surface for ARVIS.

This module defines the supported stable public contract.
Only symbols listed in __all__ are considered public API.
"""

# -----------------------------------------------------
# Core Runtime
# -----------------------------------------------------
from .os import CognitiveOS, CognitiveOSConfig
from .views.cognitive_result_view import CognitiveResultView
from .trace import DecisionTraceView
from .timeline import TimelineView
from .stability import StabilityView

# -----------------------------------------------------
# Versioning / Contract Fingerprints
# -----------------------------------------------------
from .version import (
    PACKAGE_VERSION,
    API_VERSION,
    PUBLIC_API_FINGERPRINT,
)

# -----------------------------------------------------
# IR Helpers
# -----------------------------------------------------
from .ir import build_ir_view
from .ir_canonical import canonicalize_ir, hash_ir

# -----------------------------------------------------
# Cognition
# -----------------------------------------------------
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.policy.cognitive_policy_result import CognitivePolicyResult
from arvis.cognition.policy.cognitive_signal_snapshot import CognitiveSignalSnapshot

# -----------------------------------------------------
# Memory
# -----------------------------------------------------
from arvis.memory.memory_intent import MemoryIntent
from arvis.memory.memory_gate import MemoryGate
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot
from arvis.memory.memory_long_entry import MemoryLongType

# -----------------------------------------------------
# Reasoning
# -----------------------------------------------------
from arvis.reasoning.reasoning_intent import (
    ReasoningIntent,
    ReasoningIntentType,
)

# -----------------------------------------------------
# Uncertainty
# -----------------------------------------------------
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame
from arvis.uncertainty.uncertainty_frame_registry import UncertaintyFrameRegistry

# -----------------------------------------------------
# Math
# -----------------------------------------------------
from arvis.math.lyapunov.lyapunov import (
    LyapunovState,
    LyapunovWeights,
    lyapunov_value,
    lyapunov_delta,
)

from arvis.math.core.normalization import (
    clamp,
    clamp01,
    normalize_weights,
)

from arvis.math.risk.risk_bound import (
    HoeffdingRiskBound,
    RiskBoundSnapshot,
)

# -----------------------------------------------------
# Control / Stability
# -----------------------------------------------------
from arvis.control.control_inertia import ControlInertia
from arvis.stability.stability_observer import StabilityObserver
from arvis.stability.stability_snapshot import StabilitySnapshot

# -----------------------------------------------------
# Adapters
# -----------------------------------------------------
from arvis.adapters.llm import BaseLLMAdapter, OpenAIAdapter

# -----------------------------------------------------
# Tools
# -----------------------------------------------------
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry

# -----------------------------------------------------
# Public Contract
# -----------------------------------------------------
__all__ = [
    # Core Runtime
    "CognitiveOS",
    "CognitiveOSConfig",
    "CognitiveResultView",
    "DecisionTraceView",
    "TimelineView",
    "StabilityView",
    # Versioning
    "PACKAGE_VERSION",
    "API_VERSION",
    "PUBLIC_API_FINGERPRINT",
    # IR
    "build_ir_view",
    "canonicalize_ir",
    "hash_ir",
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
    # Math
    "LyapunovState",
    "LyapunovWeights",
    "lyapunov_value",
    "lyapunov_delta",
    "clamp",
    "clamp01",
    "normalize_weights",
    "HoeffdingRiskBound",
    "RiskBoundSnapshot",
    # Control / Stability
    "ControlInertia",
    "StabilityObserver",
    "StabilitySnapshot",
    # Adapters
    "BaseLLMAdapter",
    "OpenAIAdapter",
    # Tools
    "BaseTool",
    "ToolExecutor",
    "ToolRegistry",
]
