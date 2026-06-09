# arvis/telemetry/types.py

from __future__ import annotations

from typing import TypeAlias

TelemetryPrimitive: TypeAlias = str | int | float | bool | None
TelemetryValue: TypeAlias = (
    TelemetryPrimitive | list["TelemetryValue"] | dict[str, "TelemetryValue"]
)
TelemetryAttributes: TypeAlias = dict[str, TelemetryValue]
TelemetryPayload: TypeAlias = dict[str, TelemetryValue]
