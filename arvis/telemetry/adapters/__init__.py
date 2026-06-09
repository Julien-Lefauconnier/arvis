# arvis/telemetry/adapters/__init__.py
"""
Adapters that build telemetry events from public domain contracts.

Adapters are the only telemetry components allowed to depend on domain
types, and they depend only on *public* contracts (never cognition
internals). They are kept out of ``arvis.telemetry`` top-level exports so
that importing the telemetry core never pulls in domain packages.
"""

from arvis.telemetry.adapters.core import (
    CORE_STABILITY_COMPONENT,
    core_stability_event,
)
from arvis.telemetry.adapters.errors import (
    ERROR_COMPONENT,
    degradation_event,
    error_event,
    escalation_event,
)
from arvis.telemetry.adapters.forecast import (
    FORECAST_COMPONENT,
    forecast_event,
)
from arvis.telemetry.adapters.multi import (
    MULTI_HORIZON_COMPONENT,
    multi_horizon_event,
)
from arvis.telemetry.adapters.predictive import (
    PREDICTIVE_COMPONENT,
    predictive_event,
)
from arvis.telemetry.adapters.stability import (
    STABILITY_COMPONENT,
    stability_event,
)
from arvis.telemetry.adapters.stats import (
    STATS_COMPONENT,
    stats_event,
)
from arvis.telemetry.adapters.tension import (
    SYSTEM_TENSION_COMPONENT,
    system_tension_event,
)

__all__ = [
    "CORE_STABILITY_COMPONENT",
    "core_stability_event",
    "STABILITY_COMPONENT",
    "stability_event",
    "ERROR_COMPONENT",
    "escalation_event",
    "degradation_event",
    "error_event",
    "SYSTEM_TENSION_COMPONENT",
    "system_tension_event",
    "PREDICTIVE_COMPONENT",
    "predictive_event",
    "MULTI_HORIZON_COMPONENT",
    "multi_horizon_event",
    "FORECAST_COMPONENT",
    "forecast_event",
    "STATS_COMPONENT",
    "stats_event",
]
