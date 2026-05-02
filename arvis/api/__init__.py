# arvis/api/__init__.py
"""
Public API surface for ARVIS.

This module defines the supported stable public contract.
Only symbols listed in __all__ are considered public API.
"""

# -----------------------------------------------------
# Core Runtime
# -----------------------------------------------------
# -----------------------------------------------------
# LLM Runtime (unified entrypoint)
# -----------------------------------------------------
from arvis.adapters.llm import LLMRuntimeExecutor

# -----------------------------------------------------
# Cognition
# -----------------------------------------------------
from arvis.cognition.bundle.cognitive_bundle_builder import CognitiveBundleBuilder
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.policy.cognitive_policy_result import CognitivePolicyResult
from arvis.cognition.policy.cognitive_signal_snapshot import CognitiveSignalSnapshot
from arvis.cognition.state.cognitive_state import CognitiveState

# -----------------------------------------------------
# Control / Stability
# -----------------------------------------------------
from arvis.control.control_inertia import ControlInertia
from arvis.math.core.normalization import (
    clamp,
    clamp01,
    normalize_weights,
)

# -----------------------------------------------------
# Math
# -----------------------------------------------------
from arvis.math.lyapunov.lyapunov import (
    LyapunovState,
    LyapunovWeights,
    lyapunov_delta,
    lyapunov_value,
)
from arvis.math.risk.risk_bound import (
    HoeffdingRiskBound,
    RiskBoundSnapshot,
)
from arvis.memory.memory_gate import MemoryGate

# -----------------------------------------------------
# Memory
# -----------------------------------------------------
from arvis.memory.memory_intent import MemoryIntent
from arvis.memory.memory_long_entry import MemoryLongType
from arvis.memory.memory_long_snapshot import MemoryLongSnapshot

# -----------------------------------------------------
# Reasoning
# -----------------------------------------------------
from arvis.reasoning.reasoning_intent import (
    ReasoningIntent,
    ReasoningIntentType,
)
from arvis.stability.stability_observer import StabilityObserver
from arvis.stability.stability_snapshot import StabilitySnapshot

# -----------------------------------------------------
# Tools
# -----------------------------------------------------
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry

# -----------------------------------------------------
# Uncertainty
# -----------------------------------------------------
from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame
from arvis.uncertainty.uncertainty_frame_registry import UncertaintyFrameRegistry

# -----------------------------------------------------
# Product layer
# -----------------------------------------------------
from .engine import ArvisEngine

# -----------------------------------------------------
# IR Helpers
# -----------------------------------------------------
from .ir import build_ir_view
from .ir_canonical import canonicalize_ir, hash_ir
from .os import CognitiveOS, CognitiveOSConfig
from .stability import StabilityView
from .timeline import TimelineView
from .trace import DecisionTraceView

# -----------------------------------------------------
# Versioning / Contract Fingerprints
# -----------------------------------------------------
from .version import (
    API_VERSION,
    PACKAGE_VERSION,
    PUBLIC_API_FINGERPRINT,
)
from .views.cognitive_result_view import CognitiveResultView

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
    "ArvisEngine",
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
    # LLM Runtime
    "LLMRuntimeExecutor",
    # Tools
    "BaseTool",
    "ToolExecutor",
    "ToolRegistry",
]
