# tests/errors/test_error_registry.py

from __future__ import annotations

from arvis.errors.registry import error_code_registry, iter_error_classes


def test_error_registry_has_unique_codes():
    registry = error_code_registry()

    assert registry
    assert len(registry) == len(set(registry))


def test_iter_error_classes_returns_errors():
    classes = list(iter_error_classes())

    assert classes
    assert all(cls.default_code for cls in classes)
