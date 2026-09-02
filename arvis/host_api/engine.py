# arvis/host_api/engine.py

"""Building and configuring an engine.

The engine facade, its configuration, the low-level cognitive OS a
host reaches for deterministic replay and IR control, and the
contraction monitor configuration a host passes when constructing an
engine.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.api.engine import ArvisEngine
from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.api.views.decision_status import DecisionStatus
from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
)

__all__ = [
    "ArvisEngine",
    "CognitiveOS",
    "CognitiveOSConfig",
    "CognitiveResultView",
    "ContractionMonitorCore",
    "DecisionStatus",
    "MonitorConfig",
]
