# arvis/errors/helpers.py

from __future__ import annotations

from typing import Any

from arvis.errors.base import ArvisError
from arvis.errors.manager import ErrorManager
from arvis.errors.types import ErrorPayload


def append_error(
    ctx: Any,
    error: ArvisError,
) -> ErrorPayload:
    return ErrorManager.attach(ctx, error)
