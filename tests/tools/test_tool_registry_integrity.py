# tests/tools/test_tool_registry_integrity.py

"""Governed tool registry integrity (F-004).

A governed registry is never replaced silently: duplicate names are
refused unless replacement is explicit, a frozen registry refuses any
further mutation (explicit replacement included), and the registered
surface has a deterministic, order-independent fingerprint the host
can pin after bootstrap.
"""

import json

import pytest

from arvis.api.engine import ArvisEngine
from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.registry import MANIFEST_SCHEMA_VERSION, ToolRegistry
from arvis.tools.spec import ToolSpec


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


# ---------------------------------------------------------------
# F-010-a5: governance manifest and enriched fingerprint
# ---------------------------------------------------------------


class _SpecTool(BaseTool):
    name = "spec_tool"

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def execute(self, input_data):
        return {"ok": True}


def _spec(**overrides) -> ToolSpec:
    params = {
        "name": "spec_tool",
        "description": "probe",
        "input_schema": {
            "type": "object",
            "properties": {"secret_field_name": {"type": "string"}},
        },
    }
    params.update(overrides)
    return ToolSpec(**params)


def test_manifest_structure_is_versioned_and_sorted():
    reg = ToolRegistry()
    reg.register(_ToolB())
    reg.register(_ToolA())
    manifest = reg.manifest()
    assert manifest["manifest_schema_version"] == MANIFEST_SCHEMA_VERSION
    assert [t["name"] for t in manifest["tools"]] == ["tool_a", "tool_b"]
    # Tools without a spec expose spec=None instead of being dropped.
    assert all(t["spec"] is None for t in manifest["tools"])


def test_manifest_never_carries_schema_content_in_clear():
    reg = ToolRegistry()
    reg.register(_SpecTool(_spec()))
    serialized = json.dumps(reg.manifest())
    assert "secret_field_name" not in serialized
    entry = reg.manifest()["tools"][0]["spec"]
    assert isinstance(entry["input_schema_sha256"], str)
    assert len(entry["input_schema_sha256"]) == 64
    assert entry["output_schema_sha256"] is None  # empty schema -> no hash


def test_fingerprint_is_sensitive_to_governance_flags():
    r1 = ToolRegistry()
    r1.register(_SpecTool(_spec(data_egress=False)))
    r2 = ToolRegistry()
    r2.register(_SpecTool(_spec(data_egress=True)))
    assert r1.fingerprint() != r2.fingerprint()


def test_fingerprint_is_sensitive_to_schema_content():
    r1 = ToolRegistry()
    r1.register(_SpecTool(_spec()))
    r2 = ToolRegistry()
    r2.register(
        _SpecTool(
            _spec(
                input_schema={
                    "type": "object",
                    "properties": {"other_field": {"type": "string"}},
                }
            )
        )
    )
    assert r1.fingerprint() != r2.fingerprint()


def test_fingerprint_with_specs_stays_order_independent():
    a = _SpecTool(_spec())
    r1 = ToolRegistry()
    r1.register(a)
    r1.register(_ToolB())
    r2 = ToolRegistry()
    r2.register(_ToolB())
    r2.register(a)
    assert r1.fingerprint() == r2.fingerprint()


def test_non_canonicalizable_schema_refuses_pinning():
    bad = _spec(input_schema={"type": object})  # a class is not JSON
    reg = ToolRegistry()
    reg.register(_SpecTool(bad))
    with pytest.raises(ArvisSecurityError, match="cannot be pinned"):
        reg.fingerprint()
