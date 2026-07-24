"""Host-authenticated identity is mandatory only for production effects."""

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.access.models import AuthenticatedPrincipal, Principal
from arvis.kernel_core.access.resolvers import turn_owner_resolver
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    register_syscall,
)
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec

_PROBE = "test.production.identity.effect"


def _register_probe(calls: list[str]) -> None:
    @register_syscall(
        _PROBE,
        effect=SyscallEffect.EFFECT,
        access=turn_owner_resolver(SyscallEffect.EFFECT, _PROBE),
    )
    def _probe(handler, ctx=None, causal_id=None):
        calls.append(str(causal_id))
        return SyscallResult(success=True, result={"ok": True})


def _cleanup() -> None:
    SYSCALL_REGISTRY.pop(_PROBE, None)
    SYSCALL_DESCRIPTORS.pop(_PROBE, None)


def _ctx(principal=None, *, user_id: str = "u1"):
    return SimpleNamespace(extra={}, user_id=user_id, principal=principal)


def _authenticated(user_id: str = "u1", *, source: str = "oidc"):
    return AuthenticatedPrincipal(
        user_id=user_id,
        organization_id="org-1",
        authentication_source=source,
        authentication_strength="mfa",
        session_id_hash="sha256:session",
    )


def _handler(*, require_auth: bool) -> SyscallHandler:
    return SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            require_authenticated_principal=require_auth,
        ),
    )


def test_production_effect_refuses_missing_or_bare_principal() -> None:
    calls: list[str] = []
    _register_probe(calls)
    try:
        for principal in (None, Principal(user_id="u1")):
            result = _handler(require_auth=True).handle(
                Syscall(name=_PROBE, args={"ctx": _ctx(principal)})
            )
            assert result.success is False
            assert result.error is not None
            assert (
                result.error.details.get("reason_code")
                == "authenticated_principal_required"
            )
        assert calls == []
    finally:
        _cleanup()


def test_production_effect_refuses_foreign_authenticated_principal() -> None:
    calls: list[str] = []
    _register_probe(calls)
    try:
        result = _handler(require_auth=True).handle(
            Syscall(name=_PROBE, args={"ctx": _ctx(_authenticated("other"))})
        )
        assert result.success is False
        assert calls == []
    finally:
        _cleanup()


def test_production_effect_accepts_matching_authenticated_principal() -> None:
    calls: list[str] = []
    _register_probe(calls)
    try:
        result = _handler(require_auth=True).handle(
            Syscall(name=_PROBE, args={"ctx": _ctx(_authenticated())})
        )
        assert result.success is True
        assert len(calls) == 1
    finally:
        _cleanup()


def test_local_effect_keeps_declared_user_fallback() -> None:
    calls: list[str] = []
    _register_probe(calls)
    try:
        result = _handler(require_auth=False).handle(
            Syscall(name=_PROBE, args={"ctx": _ctx(None)})
        )
        assert result.success is True
        assert len(calls) == 1
    finally:
        _cleanup()


def test_authentication_source_changes_effect_commitment() -> None:
    calls: list[str] = []
    _register_probe(calls)
    try:
        commitments: list[str] = []
        handler = _handler(require_auth=True)
        for source in ("oidc", "mtls"):
            ctx = _ctx(_authenticated(source=source))
            assert handler.handle(Syscall(name=_PROBE, args={"ctx": ctx})).success
            commitments.append(ctx.extra["syscall_intents"][0]["commitment_sha256"])
        assert commitments[0] != commitments[1]
    finally:
        _cleanup()


class _IdentityTool(BaseTool):
    name = "identity_tool"
    spec = ToolSpec(name=name, description="identity material probe")

    def execute(self, input_data):
        return {"ok": True}


def test_authenticated_identity_enters_invocation_and_snapshot(monkeypatch) -> None:
    registry = ToolRegistry()
    registry.register(_IdentityTool())
    executor = ToolExecutor(registry)
    manager = ToolManager(registry, executor)
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(
            lambda invocation, registry, **kwargs: SimpleNamespace(
                allowed=True, reason="allowed"
            )
        ),
    )
    ctx = _ctx(_authenticated(source="oidc"))
    outcome = manager.authorize(
        SimpleNamespace(
            action_decision=SimpleNamespace(tool="identity_tool", tool_payload={"x": 1})
        ),
        ctx,
    )
    assert outcome.authorized is not None
    invocation = outcome.authorized.invocation
    assert invocation.authentication_source == "oidc"
    assert invocation.authentication_strength == "mfa"
    assert (
        outcome.authorized.authorization_snapshot["authentication"]["source"] == "oidc"
    )


def test_run_as_stamps_the_exact_authenticated_principal() -> None:
    from arvis import CognitiveOS

    principal = _authenticated()
    os_ = CognitiveOS()
    captured: dict[str, object] = {}

    class _Runtime:
        def execute(self, ctx):
            captured["ctx"] = ctx
            return SimpleNamespace(
                state=None,
                result=SimpleNamespace(
                    action_decision=None,
                    execution=SimpleNamespace(can_execute=False),
                ),
            )

    os_.runtime = _Runtime()
    result = os_.run_as(principal, "hello")
    assert result.decision is None  # minimal view from the fake runtime
    assert captured["ctx"].principal is principal
