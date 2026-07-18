# tests/kernel_core/test_preauthorization_order.py
"""Pre-authorization ordering: the a8 P0 (section 8), pinned closed.

The a8 audit proved the pre-effect intent was recorded BEFORE the
business authorization existed: the first confirmed call produced an
intent with no snapshot, and a second, denied call could build its
intent from the previous call's stale snapshot left on the mutable
``ctx.extra`` channel. Campaign 6 (Lot 1) reorders the chain: the full
authorization runs before the syscall, the verdict travels sealed on
the capability, and the intent binds exactly that verdict.

These tests reproduce the audit's adversarial verifications (8.3 and
8.4) and the constat 11 confirmation scenario as regressions.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.confirmation import ConfirmationRegistry
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from arvis.tools.tool_result import PRE_EFFECT_REFUSAL


class _ProbeTool(BaseTool):
    name = "probe_tool"
    spec = ToolSpec(name="probe_tool", description="ordering probe")

    def __init__(self) -> None:
        self.executed: list[dict] = []

    def execute(self, input_data):
        self.executed.append(input_data)
        return {"ok": True}


def _rig(monkeypatch, *, verdicts: list[tuple[bool, str]]):
    """Handler + manager with a scripted policy and a digest capture."""
    registry = ToolRegistry()
    tool = _ProbeTool()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry=registry, executor=executor)
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
        ),
    )

    scripted = list(verdicts)

    def _evaluate(invocation, reg, **kwargs):
        allowed, reason = scripted.pop(0)
        return SimpleNamespace(allowed=allowed, reason=reason)

    monkeypatch.setattr(ToolPolicyEvaluator, "evaluate", staticmethod(_evaluate))

    captured: list[dict] = []
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs):
        captured.append(dict(kwargs))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)
    return handler, manager, tool, captured


def _call(handler, manager, *, payload=None):
    decision = SimpleNamespace(tool="probe_tool", tool_payload=payload or {"x": 1})
    pipeline_result = SimpleNamespace(action_decision=decision)
    ctx = SimpleNamespace(extra={}, user_id="u1")
    authorization = manager.authorize(pipeline_result, ctx)
    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": authorization,
            },
        )
    )
    return result, authorization


def test_authorization_snapshot_exists_before_intent_append(monkeypatch):
    # Audit 8.3: pre-fix, the FIRST call's intent digest carried
    # authorization_snapshot=None, because the snapshot was attached to
    # ctx.extra only during execution, after the intent was appended.
    handler, manager, tool, captured = _rig(monkeypatch, verdicts=[(True, "allowed")])
    result, authorization = _call(handler, manager)
    assert result.success is True
    assert tool.executed  # the effect ran
    assert len(captured) == 1
    snapshot = captured[0]["authorization_snapshot"]
    assert isinstance(snapshot, dict)
    assert snapshot["allowed"] is True
    assert snapshot["tool_name"] == "probe_tool"
    # The intent bound the exact material sealed on the capability.
    assert snapshot == dict(authorization.authorized.authorization_snapshot)


def test_second_denied_call_does_not_reuse_stale_snapshot(monkeypatch):
    # Audit 8.4: pre-fix, a denied second call built its intent from
    # the FIRST call's allowed snapshot left on ctx.extra. Now the
    # denied intent binds its own denial verdict.
    handler, manager, tool, captured = _rig(
        monkeypatch,
        verdicts=[(True, "allowed"), (False, "risk_above_max")],
    )
    first, _ = _call(handler, manager)
    assert first.success is True

    second, authorization = _call(handler, manager)
    assert second.success is False
    assert authorization.refusal is not None
    assert len(tool.executed) == 1  # the denied effect never ran

    assert len(captured) == 2
    denied_snapshot = captured[1]["authorization_snapshot"]
    assert isinstance(denied_snapshot, dict)
    assert denied_snapshot["allowed"] is False
    assert denied_snapshot["reason"] == "risk_above_max"
    # And it is NOT the first call's allowed material.
    assert denied_snapshot != captured[0]["authorization_snapshot"]


def test_schema_failure_releases_confirmation():
    # Audit constat 11: pre-fix, a valid confirmation was consumed when
    # the payload violated the declared input_schema, although the tool
    # was never called. Now the schema check precedes the reservation:
    # the confirmation is never touched.
    class _StrictTool(BaseTool):
        name = "strict_tool"
        spec = ToolSpec(
            name="strict_tool",
            description="schema probe",
            input_schema={
                "type": "object",
                "properties": {"n": {"type": "integer"}},
                "required": ["n"],
                "additionalProperties": False,
            },
        )

        def __init__(self) -> None:
            self.executed: list[dict] = []

        def execute(self, input_data):
            self.executed.append(input_data)
            return {"ok": True}

    registry = ToolRegistry()
    tool = _StrictTool()
    registry.register(tool)
    executor = ToolExecutor(registry)
    confirmations = ConfirmationRegistry()
    manager = ToolManager(
        registry=registry,
        executor=executor,
        confirmation_registry=confirmations,
    )

    violating_payload = {"n": "not-an-integer"}
    conf = confirmations.issue(
        tool_name="strict_tool", payload=violating_payload, principal="u1"
    )
    ctx = SimpleNamespace(
        extra={},
        user_id="u1",
        confirmation_result=SimpleNamespace(confirmation_id=conf.confirmation_id),
    )
    decision = SimpleNamespace(tool="strict_tool", tool_payload=violating_payload)
    outcome = manager.authorize(SimpleNamespace(action_decision=decision), ctx)

    assert outcome is not None
    assert outcome.refusal is not None
    assert outcome.refusal.effect_boundary == PRE_EFFECT_REFUSAL
    assert outcome.snapshot_material is not None
    assert outcome.snapshot_material["allowed"] is False
    assert outcome.snapshot_material["reason"] == "input_schema_violation"
    assert tool.executed == []  # the tool was never called
    # The confirmation was never reserved, never consumed: still pending.
    assert confirmations.pending_count() == 1
