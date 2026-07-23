# tests/tools/test_registry_deep_freeze.py

"""Deep freeze of the tool registry (external audit a13, BETA-01).

The frozen tool surface is a pinned commitment, not a flag. The registry
captures a sanitized private copy of every declared spec at registration
(canonical bytes, rebuilt schemas), snapshots the manifest at freeze()
and never recomputes the pinned fingerprint from live objects. Public
readers receive defensive copies; the governed effect path reads through
verified_spec(), which refuses fail-closed any divergence between the
private capture and the bytes pinned at registration.

The probe reproduced by the audit (mutate the caller's schema dict after
freeze(): the fingerprint changed and the active validation rules
changed) is replayed here and must now be inert.
"""

import threading

import pytest

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from tests.fixtures.builders.effect_context_builder import build_effect_context


class _SpecTool(BaseTool):
    name = "spec_tool"

    def __init__(self, spec: ToolSpec) -> None:
        self.spec = spec

    def execute(self, input_data):  # pragma: no cover - not run here
        return None


class _BareTool(BaseTool):
    name = "bare_tool"

    def execute(self, input_data):  # pragma: no cover - not run here
        return None


def _schema(required: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}},
        "required": required,
    }


def _registered(schema: dict) -> tuple[ToolRegistry, ToolSpec]:
    spec = ToolSpec(name="spec_tool", description="d", input_schema=schema)
    reg = ToolRegistry()
    reg.register(_SpecTool(spec))
    return reg, spec


# ---------------------------------------------------------------------
# The audit probe, replayed: caller-side mutation is inert
# ---------------------------------------------------------------------


def test_audit_probe_caller_mutation_after_freeze_is_inert():
    schema = _schema(required=["x"])
    reg, _spec = _registered(schema)
    pinned = reg.freeze()

    schema["required"] = ["y"]

    assert reg.frozen is True
    assert reg.fingerprint() == pinned
    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    assert governed.input_schema["required"] == ["x"]


def test_caller_mutation_before_freeze_is_inert():
    schema = _schema(required=["x"])
    reg, _spec = _registered(schema)
    before = reg.fingerprint()

    schema["required"] = ["y"]
    schema["properties"]["x"]["type"] = "string"

    assert reg.fingerprint() == before
    spec = reg.get_spec("spec_tool")
    assert spec is not None
    assert spec.input_schema["required"] == ["x"]
    assert spec.input_schema["properties"]["x"]["type"] == "integer"


def test_replacing_the_live_spec_attribute_is_inert():
    schema = _schema(required=["x"])
    spec = ToolSpec(name="spec_tool", description="d", input_schema=schema)
    tool = _SpecTool(spec)
    reg = ToolRegistry()
    reg.register(tool)
    pinned = reg.freeze()

    tool.spec = ToolSpec(
        name="spec_tool",
        description="swapped",
        input_schema=_schema(required=["y"]),
    )

    assert reg.fingerprint() == pinned
    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    assert governed.description == "d"
    assert governed.input_schema["required"] == ["x"]


# ---------------------------------------------------------------------
# Defensive views: what the registry hands out cannot reach it
# ---------------------------------------------------------------------


def test_get_spec_returns_defensive_copies():
    reg, _spec = _registered(_schema(required=["x"]))
    pinned = reg.freeze()

    view = reg.get_spec("spec_tool")
    assert view is not None
    view.input_schema["required"] = ["y"]
    view.input_schema["properties"].clear()

    again = reg.get_spec("spec_tool")
    assert again is not None
    assert again.input_schema["required"] == ["x"]
    assert "x" in again.input_schema["properties"]
    assert reg.fingerprint() == pinned


def test_list_specs_returns_defensive_copies():
    reg, _spec = _registered(_schema(required=["x"]))
    reg.freeze()

    reg.list_specs()["spec_tool"].input_schema["required"] = ["y"]

    fresh = reg.list_specs()["spec_tool"]
    assert fresh.input_schema["required"] == ["x"]


def test_manifest_documents_are_fresh_and_detached():
    reg, _spec = _registered(_schema(required=["x"]))

    loose = reg.manifest()
    loose["tools"].clear()
    loose["manifest_schema_version"] = 999
    assert reg.manifest()["tools"], "pre-freeze manifest must be rebuilt"

    pinned = reg.freeze()
    frozen_doc = reg.manifest()
    frozen_doc["tools"].clear()
    assert reg.manifest()["tools"], "frozen manifest must decode from the snapshot"
    assert reg.fingerprint() == pinned


# ---------------------------------------------------------------------
# Governed read: internal divergence refuses fail-closed
# ---------------------------------------------------------------------


def test_internal_mutation_of_the_capture_refuses_the_governed_read():
    reg, _spec = _registered(_schema(required=["x"]))
    reg.freeze()

    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    governed.input_schema["required"] = ["y"]

    with pytest.raises(ArvisSecurityError, match="diverged from the frozen"):
        reg.verified_spec("spec_tool")


def test_policy_evaluator_refuses_a_diverged_surface():
    reg, _spec = _registered(_schema(required=["x"]))
    reg.freeze()
    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    governed.output_schema["injected"] = True

    decision = ToolPolicyEvaluator.evaluate(
        ToolInvocation(
            tool_name="spec_tool",
            payload={},
            effect_context=build_effect_context(),
        ),
        reg,
    )
    assert decision.allowed is False
    assert decision.reason == "frozen_surface_diverged"


def test_authorization_service_refuses_a_diverged_surface():
    from types import SimpleNamespace

    from arvis.tools.authorization_service import (
        ToolAuthorizationFailure,
        ToolAuthorizationService,
    )

    reg, _spec = _registered(_schema(required=["x"]))
    reg.freeze()
    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    governed.input_schema["required"] = ["y"]

    service = ToolAuthorizationService(
        reg, consent_gate=None, egress_gate=None, require_gates=False
    )
    prepared = service.prepare(
        SimpleNamespace(
            action_decision=SimpleNamespace(tool="spec_tool", tool_payload={"x": 1})
        ),
        SimpleNamespace(),
    )
    assert isinstance(prepared, ToolAuthorizationFailure)
    assert prepared.reason == "frozen_surface_diverged"
    assert isinstance(prepared.error, ArvisSecurityError)


def test_effect_dispatcher_refuses_a_diverged_surface_pre_effect():
    from types import SimpleNamespace

    from arvis.tools.effect_dispatcher import EffectDispatcher
    from arvis.tools.tool_result import PRE_EFFECT_REFUSAL, ToolResult

    reg, _spec = _registered(_schema(required=["x"]))
    reg.freeze()
    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    governed.input_schema["required"] = ["y"]

    dispatcher = EffectDispatcher(reg, SimpleNamespace())
    ctx = SimpleNamespace()
    outcome = dispatcher._prepare(
        ToolInvocation(
            tool_name="spec_tool",
            payload={"x": 1},
            effect_context=build_effect_context(),
        ),
        SimpleNamespace(action_decision=SimpleNamespace(tool="spec_tool")),
        ctx,
    )
    assert isinstance(outcome, ToolResult)
    assert outcome.success is False
    assert outcome.effect_boundary == PRE_EFFECT_REFUSAL
    assert isinstance(outcome.error, ArvisSecurityError)
    assert ctx._tool_failure is True


def test_verified_spec_before_freeze_reads_the_capture():
    reg, _spec = _registered(_schema(required=["x"]))
    governed = reg.verified_spec("spec_tool")
    assert governed is not None
    assert governed.input_schema["required"] == ["x"]
    assert reg.verified_spec("absent") is None


# ---------------------------------------------------------------------
# Concurrency: mutating the source dict from another thread is inert
# ---------------------------------------------------------------------


def test_concurrent_source_mutation_never_moves_the_pinned_surface():
    schema = _schema(required=["x"])
    reg, _spec = _registered(schema)
    pinned = reg.freeze()

    stop = threading.Event()

    def _mutate() -> None:
        flip = 0
        while not stop.is_set():
            schema["required"] = ["y"] if flip % 2 else ["x"]
            schema["noise"] = flip
            flip += 1

    worker = threading.Thread(target=_mutate)
    worker.start()
    try:
        for _ in range(500):
            assert reg.fingerprint() == pinned
            governed = reg.verified_spec("spec_tool")
            assert governed is not None
            assert governed.input_schema["required"] == ["x"]
            assert "noise" not in governed.input_schema
    finally:
        stop.set()
        worker.join()


# ---------------------------------------------------------------------
# Freeze semantics
# ---------------------------------------------------------------------


def test_freeze_is_idempotent_and_returns_the_pinned_fingerprint():
    reg, _spec = _registered(_schema(required=["x"]))
    first = reg.freeze()
    second = reg.freeze()
    assert first == second
    assert reg.fingerprint() == first


def test_fingerprint_is_unchanged_by_freezing_a_sane_surface():
    reg_live, _ = _registered(_schema(required=["x"]))
    reg_frozen, _ = _registered(_schema(required=["x"]))
    pinned = reg_frozen.freeze()
    assert reg_live.fingerprint() == pinned


# ---------------------------------------------------------------------
# Registration-time refusal: an unpinnable surface never registers
# ---------------------------------------------------------------------


def test_non_canonicalizable_schema_is_refused_at_registration():
    spec = ToolSpec(
        name="spec_tool",
        description="d",
        input_schema={"marker": object()},
    )
    reg = ToolRegistry()
    with pytest.raises(ArvisSecurityError, match="non-canonicalizable"):
        reg.register(_SpecTool(spec))
    assert reg.get("spec_tool") is None
    assert reg.get_spec("spec_tool") is None


def test_non_finite_schema_value_is_refused_at_registration():
    spec = ToolSpec(
        name="spec_tool",
        description="d",
        input_schema={"maximum": float("nan")},
    )
    reg = ToolRegistry()
    with pytest.raises(ArvisSecurityError, match="non-canonicalizable"):
        reg.register(_SpecTool(spec))


def test_refused_replacement_keeps_the_previous_registration():
    reg, _spec = _registered(_schema(required=["x"]))
    poisoned = ToolSpec(
        name="spec_tool",
        description="poisoned",
        input_schema={"marker": object()},
    )
    with pytest.raises(ArvisSecurityError, match="non-canonicalizable"):
        reg.register(_SpecTool(poisoned), replace=True)
    kept = reg.get_spec("spec_tool")
    assert kept is not None
    assert kept.description == "d"


def test_non_toolspec_spec_is_refused_at_registration():
    tool = _BareTool()
    tool.spec = {"name": "bare_tool"}  # type: ignore[assignment]
    reg = ToolRegistry()
    with pytest.raises(ArvisSecurityError, match="not a ToolSpec"):
        reg.register(tool)


def test_tool_without_spec_stays_supported():
    reg = ToolRegistry()
    reg.register(_BareTool())
    pinned = reg.freeze()
    assert reg.get_spec("bare_tool") is None
    assert reg.verified_spec("bare_tool") is None
    entry = next(t for t in reg.manifest()["tools"] if t["name"] == "bare_tool")
    assert entry["spec"] is None
    assert reg.fingerprint() == pinned
