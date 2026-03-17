# arvis/kernel/pipeline/cognitive_pipeline_context.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from arvis.math.signals import RiskSignal, UncertaintySignal, DriftSignal


@dataclass
class CognitivePipelineContext:
    """
    Pure kernel context (ZKCS-safe).

    No service.
    No IO.
    No infra.

    This object only carries already-extracted cognitive inputs and
    intermediate pipeline artifacts.
    """

    user_id: str

    # -------------------------
    # Inputs
    # -------------------------
    cognitive_input: Any
    long_memory: Dict[str, Any] = field(default_factory=dict)

    # Optional precomputed / external kernel-safe inputs
    timeline: List[Any] = field(default_factory=list)
    introspection: Optional[Any] = None
    explanation: Optional[Any] = None
    previous_bundle: Optional[Any] = None
    previous_budget: Optional[Any] = None

    # -------------------------
    # Decision layer
    # -------------------------
    decision_result: Optional[Any] = None

    # -------------------------
    # Bundle layer
    # -------------------------
    bundle: Optional[Any] = None

    # -------------------------
    # Scientific / core layer
    # -------------------------
    scientific_snapshot: Optional[Any] = None
    collapse_risk: RiskSignal | float = 0.0
    uncertainty: UncertaintySignal | float | None = None
    prev_lyap: Optional[Any] = None
    cur_lyap: Optional[Any] = None
    drift_score: DriftSignal | float = 0.0
    regime: Optional[str] = None
    stable: Optional[bool] = None

    # -------------------------
    # Control layer
    # -------------------------
    control_snapshot: Optional[Any] = None
    change_budget: Optional[Any] = None

    # -------------------------
    # Gate layer
    # -------------------------
    gate_result: Optional[Any] = None

    # -------------------------
    # Execution layer
    # -------------------------
    executable_intent: Optional[Any] = None

    # -------------------------
    # Extensions
    # -------------------------
    extra: Dict[str, Any] = field(default_factory=dict)