# tests/tools/test_tool_invocation_context.py
"""Complete invocation context (F-006-a5, skeleton).

The invocation carries the real turn context: identity threaded from
the trusted context channel only (a stamped Principal, never
request-facing extra), the real turn risk as a hardening composition of
the available signals, and opaque principal/tenant/consent fields whose
meaning belongs to the host.
"""

from types import SimpleNamespace

import pytest

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.access.models import Principal
from arvis.math.signals import RiskSignal
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager, _resolve_turn_risk
from arvis.tools.registry import ToolRegistry

# ---------------------------------------------------------------
# Invocation fields
# ---------------------------------------------------------------


def test_invocation_defaults_are_safe():
    invocation = ToolInvocation(tool_name="t", payload={}, process_id="p1")
    assert invocation.principal is None
    assert invocation.tenant is None
    assert invocation.consent_granted == ()
    assert invocation.risk_score == 0.0


def test_invocation_is_immutable():
    invocation = ToolInvocation(tool_name="t", payload={}, process_id="p1")
    with pytest.raises(AttributeError):
        invocation.principal = "spoof"  # type: ignore[misc]


# ---------------------------------------------------------------
# Turn risk resolution (hardening composition)
# ---------------------------------------------------------------


def test_turn_risk_defaults_to_zero_without_signals():
    assert _resolve_turn_risk(SimpleNamespace()) == 0.0
    assert _resolve_turn_risk(SimpleNamespace(extra={})) == 0.0


def test_turn_risk_reads_declared_input_risk():
    ctx = SimpleNamespace(extra={"input_risk": 0.7})
    assert _resolve_turn_risk(ctx) == 0.7


def test_turn_risk_reads_assessed_collapse_risk():
    ctx = SimpleNamespace(extra={}, collapse_risk=RiskSignal(0.4))
    assert _resolve_turn_risk(ctx) == 0.4


def test_turn_risk_composes_by_hardening():
    # The stricter of the declared and assessed signals wins.
    ctx = SimpleNamespace(extra={"input_risk": 0.3}, collapse_risk=RiskSignal(0.8))
    assert _resolve_turn_risk(ctx) == 0.8
    ctx = SimpleNamespace(extra={"input_risk": 0.9}, collapse_risk=RiskSignal(0.2))
    assert _resolve_turn_risk(ctx) == 0.9


def test_turn_risk_ignores_invalid_signals_and_clamps():
    ctx = SimpleNamespace(extra={"input_risk": True})  # bool excluded
    assert _resolve_turn_risk(ctx) == 0.0
    ctx = SimpleNamespace(extra={"input_risk": 3.0})
    assert _resolve_turn_risk(ctx) == 1.0


# ---------------------------------------------------------------
# Manager threading (identity from the trusted channel only)
# ---------------------------------------------------------------


def _run_manager_and_capture_invocation(ctx):
    """Run ToolManager.run with a policy stub capturing the invocation."""
    from arvis.adapters.tools.policy import ToolPolicyEvaluator
    from arvis.tools.executor import ToolExecutor
    from arvis.tools.manager import ToolManager
    from arvis.tools.registry import ToolRegistry

    registry = ToolRegistry()

    class _ProbeTool:
        name = "t"
        spec = None

        def validate(self, payload):
            return None

        def execute(self, payload):
            return {"ok": True}

    registry.register(_ProbeTool())
    manager = ToolManager(registry, ToolExecutor(registry))

    captured: dict = {}
    original = ToolPolicyEvaluator.evaluate

    def _capture(invocation, reg, **kwargs):
        captured["invocation"] = invocation
        return SimpleNamespace(allowed=False, reason="captured")

    ToolPolicyEvaluator.evaluate = staticmethod(_capture)  # type: ignore[method-assign]
    try:
        decision = SimpleNamespace(tool="t", tool_payload={})
        result = SimpleNamespace(action_decision=decision)
        manager.run(result, ctx)
    finally:
        ToolPolicyEvaluator.evaluate = original  # type: ignore[method-assign]
    return captured["invocation"]


def test_manager_threads_stamped_principal_and_tenant():
    ctx = SimpleNamespace(
        extra={"input_risk": 0.5},
        user_id="u1",
        principal=Principal(user_id="u1", organization_id="org-9"),
    )
    invocation = _run_manager_and_capture_invocation(ctx)
    assert invocation.user_id == "u1"
    assert invocation.principal == "u1"
    assert invocation.tenant == "org-9"
    assert invocation.risk_score == 0.5


def test_manager_leaves_identity_empty_without_stamp():
    # No stamped Principal: opaque identity fields stay None; the bare
    # user_id still travels for owner scoping.
    ctx = SimpleNamespace(extra={}, user_id="u1")
    invocation = _run_manager_and_capture_invocation(ctx)
    assert invocation.user_id == "u1"
    assert invocation.principal is None
    assert invocation.tenant is None
    assert invocation.consent_granted == ()


def test_manager_never_reads_identity_from_extra():
    # Identity smuggled through the request-facing extra channel is
    # never read (F-001 campaign 2 doctrine).
    ctx = SimpleNamespace(
        extra={"principal": Principal(user_id="attacker")},
        user_id="u1",
    )
    invocation = _run_manager_and_capture_invocation(ctx)
    assert invocation.principal is None


# ---------------------------------------------------------------
# Campaign 6, Lot 7: the invocation fields are filled (a8 section 13)
# ---------------------------------------------------------------


def test_audit_required_travels_from_the_spec(monkeypatch):
    from arvis.tools.spec import ToolSpec

    registry = ToolRegistry()

    class _AuditedTool:
        name = "audited"
        spec = ToolSpec(name="audited", description="", audit_required=True)

        def validate(self, payload):
            return None

        def execute(self, payload):
            return {"ok": True}

    registry.register(_AuditedTool())
    manager = ToolManager(registry, ToolExecutor(registry))
    captured: dict = {}

    def _capture(invocation, reg, **kwargs):
        captured["invocation"] = invocation
        return SimpleNamespace(allowed=False, reason="captured")

    monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_capture))
    decision = SimpleNamespace(tool="audited", tool_payload={})
    manager.authorize(
        SimpleNamespace(action_decision=decision),
        SimpleNamespace(extra={}, user_id="u1"),
    )
    assert captured["invocation"].audit_required is True


def test_consent_granted_comes_from_the_trusted_channel(monkeypatch):
    registry = ToolRegistry()

    class _T:
        name = "t"
        spec = None

        def validate(self, payload):
            return None

        def execute(self, payload):
            return {"ok": True}

    registry.register(_T())
    manager = ToolManager(registry, ToolExecutor(registry))
    captured: dict = {}

    def _capture(invocation, reg, **kwargs):
        captured["invocation"] = invocation
        return SimpleNamespace(allowed=False, reason="captured")

    monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_capture))
    decision = SimpleNamespace(tool="t", tool_payload={})
    ctx = SimpleNamespace(
        extra={"consent_granted": ["spoofed_via_extra"]},
        user_id="u1",
        consent_granted=("mail_send", "calendar_write", 42),
    )
    manager.authorize(SimpleNamespace(action_decision=decision), ctx)
    inv = captured["invocation"]
    # Trusted composition channel only, string keys only; the
    # request-facing extra never feeds it.
    assert inv.consent_granted == ("mail_send", "calendar_write")


def test_idempotency_key_is_deterministic_per_logical_action(monkeypatch):
    registry = ToolRegistry()

    class _T:
        name = "t"
        spec = None

        def validate(self, payload):
            return None

        def execute(self, payload):
            return {"ok": True}

    registry.register(_T())
    manager = ToolManager(registry, ToolExecutor(registry))
    captured: list = []

    def _capture(invocation, reg, **kwargs):
        captured.append(invocation)
        return SimpleNamespace(allowed=False, reason="captured")

    monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_capture))

    def _authorize(payload):
        decision = SimpleNamespace(tool="t", tool_payload=payload)
        manager.authorize(
            SimpleNamespace(action_decision=decision),
            SimpleNamespace(extra={}, user_id="u1"),
        )

    _authorize({"target": "A"})
    _authorize({"target": "A"})
    _authorize({"target": "B"})
    keys = [inv.idempotency_key for inv in captured]
    assert keys[0] is not None and keys[0].startswith("idem:")
    # Same logical action (retry): same key; different payload: new key.
    assert keys[0] == keys[1]
    assert keys[2] != keys[0]
