# arvis/errors/helpers.py

from __future__ import annotations

from typing import Any

from arvis.errors.base import ArvisError


def append_error(
    ctx: Any,
    error: ArvisError,
) -> None:
    ctx.extra.setdefault("errors", []).append(error.to_dict())

    if error.degraded:
        ctx.extra.setdefault("degraded", []).append(error.code)

    if error.severity.value in {"fatal", "error"}:
        ctx.extra.setdefault("kernel_failures", []).append(error.code)
