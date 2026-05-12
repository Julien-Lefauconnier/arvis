# arvis/errors/registry.py

from __future__ import annotations

import inspect
from collections.abc import Iterator

import arvis.errors as errors_pkg
from arvis.errors.base import ArvisError


def iter_error_classes() -> Iterator[type[ArvisError]]:
    for _, obj in inspect.getmembers(errors_pkg):
        if (
            inspect.isclass(obj)
            and issubclass(obj, ArvisError)
            and obj is not ArvisError
        ):
            yield obj


def error_code_registry() -> dict[str, type[ArvisError]]:
    registry: dict[str, type[ArvisError]] = {}

    for error_cls in iter_error_classes():
        code = error_cls.default_code

        if code in registry:
            raise RuntimeError(
                f"Duplicate ARVIS error code: {code} "
                f"({registry[code].__name__}, {error_cls.__name__})"
            )

        registry[code] = error_cls

    return registry
