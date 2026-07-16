# tests/tools/test_tool_registry_integrity.py

"""Governed tool registry integrity (F-004).

A governed registry is never replaced silently: duplicate names are
refused unless replacement is explicit, a frozen registry refuses any
further mutation (explicit replacement included), and the registered
surface has a deterministic, order-independent fingerprint the host
can pin after bootstrap.
"""

import pytest

from arvis.api.engine import ArvisEngine
from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.registry import ToolRegistry


class _ToolA(BaseTool):
    name = "tool_a"

    def execute(self, input_data):
        return {"ok": True}


class _ToolA2(BaseTool):
    name = "tool_a"

    def execute(self, input_data):
        return {"ok": True, "v": 2}


class _ToolB(BaseTool):
    name = "tool_b"

    def execute(self, input_data):
        return {"ok": True}


def test_duplicate_registration_is_refused():
    reg = ToolRegistry()
    reg.register(_ToolA())
    with pytest.raises(ArvisSecurityError, match="already registered"):
        reg.register(_ToolA2())
    assert isinstance(reg.get("tool_a"), _ToolA)


def test_explicit_replacement_is_allowed():
    reg = ToolRegistry()
    reg.register(_ToolA())
    reg.register(_ToolA2(), replace=True)
    assert isinstance(reg.get("tool_a"), _ToolA2)


def test_frozen_registry_refuses_registration():
    reg = ToolRegistry()
    reg.register(_ToolA())
    reg.freeze()
    assert reg.frozen is True
    with pytest.raises(ArvisSecurityError, match="frozen"):
        reg.register(_ToolB())
    with pytest.raises(ArvisSecurityError, match="frozen"):
        reg.register(_ToolA2(), replace=True)


def test_fingerprint_is_deterministic_and_order_independent():
    r1 = ToolRegistry()
    r1.register(_ToolA())
    r1.register(_ToolB())
    r2 = ToolRegistry()
    r2.register(_ToolB())
    r2.register(_ToolA())
    assert r1.fingerprint() == r2.fingerprint()
    r3 = ToolRegistry()
    r3.register(_ToolA())
    assert r3.fingerprint() != r1.fingerprint()


def test_freeze_returns_fingerprint():
    reg = ToolRegistry()
    reg.register(_ToolA())
    assert reg.freeze() == reg.fingerprint()


def test_engine_freeze_tools_pins_the_surface():
    engine = ArvisEngine()
    engine.register_tool(_ToolA())
    fingerprint = engine.freeze_tools()
    assert isinstance(fingerprint, str) and len(fingerprint) == 64
    with pytest.raises(ArvisSecurityError, match="frozen"):
        engine.register_tool(_ToolB())
