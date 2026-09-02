# arvis/host_api/control.py

"""PROVISIONAL: the host-side cognitive control runtime.

The control engine and its strategies (exploration, hysteresis,
regime policy) a host may run as a component of its own product
surface. This module is PROVISIONAL: it tracks the most active
research area of the kernel, so its surface may change in a minor
release. Changes are documented in the changelog; no deprecation
window is guaranteed. Every other host_api module is stable.

What this engine is NOT (campaign SURFACE, DM-S3): it is not on the
kernel verdict path. The gate decision stack of the pipeline is the
only producer of the governed verdict; ``CognitiveControlEngine`` is
a host-side component whose recommendations never override, feed or
shadow that stack, and a structural contract test keeps the kernel
from ever importing it
(``tests/contracts/test_control_engine_isolation.py``).

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
