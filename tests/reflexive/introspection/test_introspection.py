# tests/reflexive/introspection/test_introspection.py
"""The introspection overview must describe things that exist.

The previous version of this file asserted nothing (an empty test and
an ``is not None``). Meanwhile the overview described four world-model
modules and a ``global_stability_monitor`` that did not exist anywhere
in the repository, and the attestation sealed that prose (audit A3,
2026-08). These tests are the ratchet: every module path a static
declaration names must import, and declarations must say what they are.
"""

from __future__ import annotations

import importlib
from typing import Any

from arvis.reflexive.introspection.arvis_introspection_service import (
    ArvisIntrospectionService,
)


def _overview() -> dict[str, Any]:
    return ArvisIntrospectionService().build_system_overview()


def test_overview_declares_its_provenance() -> None:
    overview = _overview()
    assert overview["provenance"] == "static_declaration"


def test_every_declared_module_path_exists() -> None:
    overview = _overview()
    missing: list[str] = []
    for section in overview.values():
        if not isinstance(section, dict):
            continue
        for component in section.get("components", []):
            module = component.get("module")
            if not isinstance(module, str) or "." not in module:
                continue
            try:
                importlib.import_module(module)
            except ImportError:
                missing.append(module)
    assert not missing, (
        "the introspection overview describes modules that do not exist: "
        f"{missing}. A self-description that attests to phantom modules "
        "is worse than none."
    )


def test_math_declaration_reports_execution_status_honestly() -> None:
    """Each math component carries an explicit status, and the modules
    the default engine does not evaluate are marked host_driven."""
    math = _overview()["math"]
    assert math["kind"] == "static_declaration"
    statuses = {c["module"]: c["status"] for c in math["components"]}
    assert set(statuses.values()) <= {"default_path", "host_driven"}
    assert statuses["arvis.math.lyapunov.lyapunov_gate"] == "default_path"
    assert statuses["arvis.kernel.gate.input_risk"] == "default_path"


def test_world_model_section_stays_removed() -> None:
    assert "world_model" not in _overview(), (
        "the world-model introspector described modules that never "
        "existed; it must not return without an implementation to describe"
    )
