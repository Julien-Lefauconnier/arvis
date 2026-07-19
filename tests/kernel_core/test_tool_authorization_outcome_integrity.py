"""Campaign 7 Lot 3: strict authorization outcome integrity.

The pre-effect intent and the effect must consume one exact transport object.
Generic wrappers, partial outcomes and capabilities not owned by the configured
manager are refused before the intent commitment is computed.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from arvis.adapters.tools.authorization_snapshot import ToolAuthorizationSnapshot
from arvis.adapters.tools.invocation import ToolInvocation
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.authorized_invocation import AuthorizedInvocation
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolAuthorizationOutcome, ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec
from arvis.tools.tool_result import PRE_EFFECT_REFUSAL, ToolResult
from tests.fixtures.builders.effect_context_builder import build_effect_context


class _ProbeTool(BaseTool):
    def __init__(self, name: str = "outcome_probe") -> None:
        self.name = name
        self.spec = ToolSpec(name=name, description="strict outcome probe")
        self.payloads: list[dict[str, Any]] = []

    def execute(self, input_data: dict[str, Any]) -> Any:
        payload = input_data.get("tool_payload", {})
        self.payloads.append(dict(payload))
        return {"ok": True}


def _ctx() -> Any:
    return SimpleNamespace(extra={}, user_id="u1")


def _pipeline_result(payload: dict[str, Any] | None = None) -> Any:
    return SimpleNamespace(
        action_decision=SimpleNamespace(
            tool="outcome_probe",
            tool_payload=payload or {"x": 1},
        )
    )


def _rig(
    *additional_tools: _ProbeTool,
) -> tuple[SyscallHandler, ToolManager, _ProbeTool]:
    registry = ToolRegistry()
    tool = _ProbeTool()
    registry.register(tool)
    for additional in additional_tools:
        registry.register(additional)
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
    return handler, manager, tool


def _denial_snapshot(*, tool_name: str = "outcome_probe") -> ToolAuthorizationSnapshot:
    return ToolAuthorizationSnapshot(
        tool_name=tool_name,
        allowed=False,
        reason="denied",
        principal="u1",
        tenant=None,
        risk_score=0.0,
        confirmed=False,
        confirmation_commitment=None,
    )


def _refusal(*, tool_name: str = "outcome_probe") -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        success=False,
        effect_boundary=PRE_EFFECT_REFUSAL,
    )


def test_outcome_requires_exactly_one_authorization_path() -> None:
    invocation = ToolInvocation(
        tool_name="outcome_probe",
        payload={"x": 1},
        effect_context=build_effect_context(process_id="p1"),
    )
    capability = AuthorizedInvocation(invocation=invocation, nonce="manual")

    with pytest.raises(ValueError, match="exactly one"):
        ToolAuthorizationOutcome()

    with pytest.raises(ValueError, match="exactly one"):
        ToolAuthorizationOutcome(
            authorized=capability,
            refusal=_refusal(),
            refusal_snapshot=_denial_snapshot(),
        )


def test_success_outcome_requires_exact_authorized_invocation() -> None:
    with pytest.raises(TypeError, match="exact AuthorizedInvocation"):
        ToolAuthorizationOutcome(authorized=SimpleNamespace())  # type: ignore[arg-type]


def test_refusal_outcome_requires_matching_denial_snapshot() -> None:
    with pytest.raises(TypeError, match="ToolAuthorizationSnapshot"):
        ToolAuthorizationOutcome(
            refusal=_refusal(),
            refusal_snapshot={"allowed": False},  # type: ignore[arg-type]
        )

    allowed = ToolAuthorizationSnapshot(
        tool_name="outcome_probe",
        allowed=True,
        reason="allowed",
        principal="u1",
        tenant=None,
        risk_score=0.0,
        confirmed=False,
        confirmation_commitment=None,
    )
    with pytest.raises(ValueError, match="cannot be allowed"):
        ToolAuthorizationOutcome(refusal=_refusal(), refusal_snapshot=allowed)

    with pytest.raises(ValueError, match="same tool"):
        ToolAuthorizationOutcome(
            refusal=_refusal(tool_name="outcome_probe"),
            refusal_snapshot=_denial_snapshot(tool_name="other"),
        )


def test_snapshot_material_is_derived_from_the_selected_strict_path() -> None:
    denial = _denial_snapshot()
    outcome = ToolAuthorizationOutcome(
        refusal=_refusal(),
        refusal_snapshot=denial,
    )

    first = outcome.snapshot_material
    first["principal"] = "attacker"

    assert outcome.snapshot_material == denial.to_material()
    assert outcome.snapshot_material["principal"] == "u1"


def test_handler_reads_allowed_snapshot_only_from_owned_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler, manager, tool = _rig()
    ctx = _ctx()
    pipeline_result = _pipeline_result()
    outcome = manager.authorize(pipeline_result, ctx)
    assert isinstance(outcome, ToolAuthorizationOutcome)
    assert outcome.authorized is not None

    captured: list[dict[str, Any] | None] = []
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs: Any) -> str:
        captured.append(kwargs.get("authorization_snapshot"))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": outcome,
            },
        )
    )

    assert result.success is True
    assert tool.payloads == [{"x": 1}]
    assert captured == [dict(outcome.authorized.authorization_snapshot)]


def test_cloned_capability_with_forged_snapshot_is_refused_before_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler, manager, tool = _rig()
    ctx = _ctx()
    pipeline_result = _pipeline_result()
    legitimate = manager.authorize(pipeline_result, ctx)
    assert isinstance(legitimate, ToolAuthorizationOutcome)
    assert legitimate.authorized is not None

    forged_snapshot = {
        **dict(legitimate.authorized.authorization_snapshot),
        "principal": "attacker",
        "tenant": "forged-tenant",
    }
    cloned = AuthorizedInvocation(
        invocation=legitimate.authorized.invocation,
        authorization_snapshot=forged_snapshot,
        nonce=legitimate.authorized.nonce,
        capability_format_version=legitimate.authorized.capability_format_version,
    )
    forged_outcome = ToolAuthorizationOutcome(authorized=cloned)

    captured: list[dict[str, Any] | None] = []
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs: Any) -> str:
        captured.append(kwargs.get("authorization_snapshot"))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": forged_outcome,
            },
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.details["reason_code"] == (
        "untrusted_tool_authorization_outcome"
    )
    assert tool.payloads == []
    assert captured == []
    assert ctx.extra.get("syscall_intents", []) == []


def test_forged_principal_in_generic_wrapper_never_enters_intent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    handler, manager, tool = _rig()
    ctx = _ctx()
    pipeline_result = _pipeline_result()
    legitimate = manager.authorize(pipeline_result, ctx)
    assert isinstance(legitimate, ToolAuthorizationOutcome)
    assert legitimate.authorized is not None

    wrapper = SimpleNamespace(
        authorized=legitimate.authorized,
        refusal=None,
        snapshot_material={
            **dict(legitimate.authorized.authorization_snapshot),
            "principal": "attacker",
            "tenant": "forged-tenant",
        },
    )

    captured: list[dict[str, Any] | None] = []
    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _capture(**kwargs: Any) -> str:
        captured.append(kwargs.get("authorization_snapshot"))
        return real_digest(**kwargs)

    monkeypatch.setattr(handler_module, "effect_engagement_digest", _capture)

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": wrapper,
            },
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "invalid_syscall_args"
    assert tool.payloads == []
    assert captured == []
    assert ctx.extra.get("syscall_intents", []) == []


def test_handler_uses_kernel_owned_outcome_copy_across_intent_and_effect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = _ProbeTool("other_probe")
    handler, manager, tool = _rig(other)
    ctx = _ctx()
    first_result = _pipeline_result({"target": "first"})
    second_result = SimpleNamespace(
        action_decision=SimpleNamespace(
            tool="other_probe",
            tool_payload={"target": "second"},
        )
    )
    first = manager.authorize(first_result, ctx)
    second = manager.authorize(second_result, ctx)
    assert isinstance(first, ToolAuthorizationOutcome)
    assert isinstance(second, ToolAuthorizationOutcome)
    assert first.authorized is not None
    assert second.authorized is not None

    import arvis.kernel_core.syscalls.syscall_handler as handler_module

    real_digest = handler_module.effect_engagement_digest

    def _swap_original_after_intent_material_is_selected(**kwargs: Any) -> str:
        # Simulates a retained caller reference mutating the original transport
        # during a callback in the intent phase. The kernel-owned copy must keep
        # the first capability for the subsequent syscall body.
        object.__setattr__(first, "authorized", second.authorized)
        return real_digest(**kwargs)

    monkeypatch.setattr(
        handler_module,
        "effect_engagement_digest",
        _swap_original_after_intent_material_is_selected,
    )

    result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": first_result,
                "ctx": ctx,
                "authorization": first,
            },
        )
    )

    assert result.success is True
    assert tool.payloads == [{"target": "first"}]
    assert other.payloads == []
