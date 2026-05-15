# arvis/errors/types.py

from __future__ import annotations

from typing import TypeAlias

ErrorPrimitive: TypeAlias = str | int | float | bool | None
ErrorDetails: TypeAlias = dict[str, ErrorPrimitive]
ErrorPayloadValue: TypeAlias = (
    ErrorPrimitive | list["ErrorPayloadValue"] | dict[str, "ErrorPayloadValue"]
)
ErrorPayload: TypeAlias = dict[str, ErrorPayloadValue]
