# arvis/host_api/control.py

"""PROVISIONAL: the cognitive control runtime.

The control engine and its strategies (exploration, hysteresis,
regime policy) a host may run as a component of its own product
surface. This module is PROVISIONAL: it tracks the most active
research area of the kernel, so its surface may change in a minor
release. Changes are documented in the changelog; no deprecation
window is guaranteed. Every other host_api module is stable.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.cognition.control.cognitive_control_engine import (
    CognitiveControlDeps,
    CognitiveControlEngine,
)
from arvis.cognition.control.exploration_controller import ExplorationController
from arvis.cognition.control.mode_hysteresis import ModeHysteresis
from arvis.cognition.control.regime_policy import CognitiveRegimePolicy

__all__ = [
    "CognitiveControlDeps",
    "CognitiveControlEngine",
    "CognitiveRegimePolicy",
    "ExplorationController",
    "ModeHysteresis",
]
