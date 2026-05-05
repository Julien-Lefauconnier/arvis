# arvis/kernel/pipeline/stages/gate/models.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.confidence.system_confidence import SystemConfidenceInputs


@dataclass
class StabilityEnvelope:
    delta_w: float | None
    global_safe: bool
    switching_safe: bool
    w_bound_ratio: float | None
    hard_block: bool
    hard_reason: str | None


@dataclass
class CompositeMetrics:
    prev_slow: Any
    cur_slow: Any
    prev_symbolic: Any
    cur_symbolic: Any
    delta_w: float | None
    w_prev: float | None
    w_current: float | None


@dataclass
class StabilityAssessment:
    global_safe: bool
    switching_safe: bool
    w_ratio: float | None
    adaptive_metrics: AdaptiveSnapshot | None
    recovery_detected: bool
    composite_recommendation: str | None
    switching_metrics: dict[str, Any]
    envelope: StabilityEnvelope
    confidence_inputs: SystemConfidenceInputs
    system_confidence: float


@dataclass
class GateDecisionResult:
    verdict: Any
    pre_verdict: Any
    kernel_result: Any
    stability_certificate: dict[str, Any]
