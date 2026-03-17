#  arvis/cognition/state/cogntive_state.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Any

from arvis.stability import GlobalForecastSnapshot
from arvis.reflexive.irg_latent_state import IRGLatentState


@dataclass(frozen=True)
class CognitiveRiskSnapshot:
    """
    Canonical risk aggregation snapshot.
    """

    mh_risk: float
    world_risk: float
    forecast_risk: float
    fused_risk: float
    smoothed_risk: float


@dataclass(frozen=True)
class CognitiveState:
    """
    Unified cognitive state (ARVIS unified model v1).

    Immutable.
    ZKCS-safe.
    Numeric-only.
    """

    # ------------------------
    # Core bundle reference
    # ------------------------
    bundle_id: str

    # ------------------------
    # Stability
    # ------------------------
    dv: float
    collapse_risk: CognitiveRiskSnapshot

    # ------------------------
    # World / Forecast
    # ------------------------
    world_prediction: Optional[Any]
    forecast: Optional[GlobalForecastSnapshot]

    # ------------------------
    # Reflexive geometry
    # ------------------------
    irg: Optional[IRGLatentState]

    # ------------------------
    # Control parameters
    # ------------------------
    epsilon: float

    # ------------------------
    # Flags
    # ------------------------
    early_warning: bool