# arvis/errors/context.py

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass, field
from typing import Any, Protocol, TypeAlias

ErrorExtra: TypeAlias = MutableMapping[str, Any]


class ErrorContextLike(Protocol):
    extra: MutableMapping[str, Any]


@dataclass(slots=True)
class DefaultErrorContext:
    """
    Minimal context container compatible with ErrorManager.
    """

    extra: MutableMapping[str, Any] = field(default_factory=dict)


def ensure_error_extra(ctx: Any) -> MutableMapping[str, Any]:
    extra = getattr(ctx, "extra", None)

    if extra is None:
        ctx.extra = {}
        extra = ctx.extra

    if not isinstance(extra, MutableMapping):
        raise TypeError("ctx.extra must be a mutable mapping")

    return extra


def has_error_extra(ctx: Any) -> bool:
    return isinstance(getattr(ctx, "extra", None), MutableMapping)
