# arvis/errors/types.py

from __future__ import annotations

from typing import TypeAlias

ErrorPrimitive: TypeAlias = str | int | float | bool | None
ErrorDetails: TypeAlias = dict[str, ErrorPrimitive]
ErrorPayload: TypeAlias = dict[str, ErrorPrimitive | ErrorDetails | list[str]]
