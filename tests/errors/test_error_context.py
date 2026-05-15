# tests/errors/test_error_context.py

from __future__ import annotations

import pytest

from arvis.errors.context import (
    DefaultErrorContext,
    ensure_error_extra,
    has_error_extra,
)


class DummyContext:
    pass


class InvalidContext:
    extra = []


def test_default_error_context_has_mutable_extra():
    ctx = DefaultErrorContext()

    assert isinstance(ctx.extra, dict)
    assert ctx.extra == {}


def test_ensure_error_extra_creates_extra():
    ctx = DummyContext()

    extra = ensure_error_extra(ctx)

    assert isinstance(extra, dict)
    assert ctx.extra == {}


def test_ensure_error_extra_returns_existing_mapping():
    ctx = DummyContext()
    ctx.extra = {"x": 1}

    extra = ensure_error_extra(ctx)

    assert extra is ctx.extra


def test_ensure_error_extra_rejects_invalid_extra():
    ctx = InvalidContext()

    with pytest.raises(TypeError):
        ensure_error_extra(ctx)


def test_has_error_extra_returns_true():
    ctx = DummyContext()
    ctx.extra = {}

    assert has_error_extra(ctx) is True


def test_has_error_extra_returns_false():
    ctx = DummyContext()

    assert has_error_extra(ctx) is False


def test_has_error_extra_rejects_non_mapping():
    ctx = DummyContext()
    ctx.extra = []

    assert has_error_extra(ctx) is False
