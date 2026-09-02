# arvis/api/runtime_mode.py

"""Closed runtime mode set (audit F-008).

runtime_mode used to be a free string: only the exact value
"production" activated the production protections, so "prod",
"Production" or "production-strict" silently ran with a permissive
posture. The set is now closed and unknown values are refused at
configuration time.
"""

from __future__ import annotations

from enum import StrEnum


class RuntimeMode(StrEnum):
    """Runtime profile of a CognitiveOS instance.

    LOCAL is the permissive default for embedding and development,
    TEST and RESEARCH are explicit non-production postures
    (currently behaviorally identical to LOCAL: no code path branches
    on them yet; they exist so a host can DECLARE the posture, and
    they stay in the frozen surface under the beta contract), and
    PRODUCTION activates the closed profile (host runtime controls
    rejected, deny-by-default tool gates, frozen tool registry).
    """

    LOCAL = "local"
    TEST = "test"
    RESEARCH = "research"
    PRODUCTION = "production"


def coerce_runtime_mode(value: RuntimeMode | str) -> RuntimeMode:
    """Coerce a configured runtime mode, refusing unknown values."""
    if isinstance(value, RuntimeMode):
        return value
    try:
        return RuntimeMode(value)
    except ValueError as exc:
        known = ", ".join(sorted(mode.value for mode in RuntimeMode))
        raise ValueError(
            f"unknown runtime_mode {value!r}; known modes: {known}"
        ) from exc


__all__ = ["RuntimeMode", "coerce_runtime_mode"]
