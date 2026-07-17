# tests/kernel_core/test_effect_engagement.py
"""Pre-effect engagement of exact parameters (P0-3-a6).

The intent carries `commitment_sha256`, computed BEFORE the effect: it
binds the syscall, its materialized redacted arguments, the principal,
the tenant, the turn owner and the authorization outcome. Two effects
with different parameters and identical results yield different
engagement digests, hence different journal digests and different
composed commitments. Only hashes enter the journal, never content.
"""

from types import SimpleNamespace

from arvis.api.commitment import compose_global_commitment, syscall_journal_digest
from arvis.kernel_core.access.models import AccessContext, Principal
from arvis.kernel_core.syscalls.engagement import (
    deep_material,
    effect_engagement_digest,
)
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall, SyscallResult
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.kernel_core.syscalls.syscall_registry import (
    SYSCALL_DESCRIPTORS,
    SYSCALL_REGISTRY,
    SyscallEffect,
    register_syscall,
)

_PROBE = "test.engagement.effect"
_H = "a" * 64


def _digest(**overrides):
    params = {
        "syscall_name": "tool.execute",
        "args": {"command": "DELETE A"},
        "principal_user_id": "u1",
        "principal_organization_id": None,
        "turn_user_id": "u1",
        "authorization_reason_code": None,
    }
    params.update(overrides)
    return effect_engagement_digest(**params)


# ---------------------------------------------------------------
# Digest properties
# ---------------------------------------------------------------


def test_engagement_digest_is_deterministic():
    assert _digest() == _digest()


def test_engagement_digest_binds_the_arguments():
    # Audit scenario: DELETE A and DELETE B, same result, must not
    # collapse into the same hash.
    a = _digest(args={"command": "DELETE A"})
    b = _digest(args={"command": "DELETE B"})
    assert a != b


def test_engagement_digest_binds_identity_and_authorization():
    base = _digest()
    assert _digest(principal_user_id="u2") != base
    assert _digest(principal_organization_id="org-9") != base
    assert _digest(turn_user_id="u2") != base
    assert _digest(authorization_reason_code="owner_match") != base


def test_engagement_digest_excludes_the_trusted_ctx_object():
    # Identity is engaged explicitly; the ctx object itself never
    # enters the material, so two structurally different ctx carriers
    # with the same identity engage identically.
    a = _digest(args={"x": 1, "ctx": SimpleNamespace(user_id="u1", extra={})})
    b = _digest(args={"x": 1, "ctx": SimpleNamespace(user_id="u1")})
    assert a == b


def test_deep_material_distinguishes_object_payloads():
    # P1-12 direction: unlike the type-only fallback, object attributes
    # stay distinguishable in the engagement material.
    class Command:
        def __init__(self, target: str) -> None:
            self.target = target

    a = deep_material(Command("A"))
    b = deep_material(Command("B"))
    assert a != b
    assert a["fields"]["target"] == "A"


def test_deep_material_is_cycle_safe_and_depth_capped():
    node = SimpleNamespace(name="n")
    node.self_ref = node
    material = deep_material(node)
    assert material["fields"]["name"] == "n"
    # The cycle collapses to a type marker instead of recursing.
    assert material["fields"]["self_ref"] == {"__type__": "SimpleNamespace"}


# ---------------------------------------------------------------
# End to end: intent digest through the real boundary
# ---------------------------------------------------------------


def _allow_resolver(args, services):
    return AccessContext(
        principal=Principal(user_id="u1"),
        effect=SyscallEffect.EFFECT,
        resource_owner_id="u1",
        syscall_name=_PROBE,
    )


def _run_probe(command: str):
    def _fn(handler, command, ctx=None, causal_id=None, **kwargs):
        return SyscallResult(success=True, result={"ok": True})

    register_syscall(_PROBE, effect=SyscallEffect.EFFECT, access=_allow_resolver)(_fn)
    try:
        handler = SyscallHandler(
            runtime_state=None, scheduler=None, services=KernelServiceRegistry()
        )
        ctx = SimpleNamespace(extra={}, user_id="u1")
        result = handler.handle(
            Syscall(name=_PROBE, args={"command": command, "ctx": ctx})
        )
        assert result.success is True
        return ctx
    finally:
        SYSCALL_REGISTRY.pop(_PROBE, None)
        SYSCALL_DESCRIPTORS.pop(_PROBE, None)


def test_different_effect_arguments_change_the_composed_commitment():
    # Same syscall, same result, different command: the intents differ,
    # the journal digests differ, the composed commitments differ.
    ctx_a = _run_probe("DELETE A")
    ctx_b = _run_probe("DELETE B")

    intent_a = ctx_a.extra["syscall_intents"][0]
    intent_b = ctx_b.extra["syscall_intents"][0]
    assert intent_a["commitment_sha256"] != intent_b["commitment_sha256"]

    digest_a = syscall_journal_digest(
        ctx_a.extra["syscall_intents"], ctx_a.extra["syscall_results"]
    )
    digest_b = syscall_journal_digest(
        ctx_b.extra["syscall_intents"], ctx_b.extra["syscall_results"]
    )
    assert digest_a != digest_b

    def _compose(journal_digest):
        return compose_global_commitment(
            ir_hash="i",
            timeline_commitment="t",
            commitment_inputs={
                "registry_fingerprint": _H,
                "config_fingerprint": _H,
                "policies_fingerprint": _H,
                "syscall_journal_sha256": journal_digest,
            },
        )

    assert _compose(digest_a) != _compose(digest_b)


def test_engagement_material_never_leaks_content():
    ctx = _run_probe("secret_command_body")
    intent = ctx.extra["syscall_intents"][0]
    assert "secret_command_body" not in str(intent)
    assert "secret_command_body" not in str(ctx.extra["syscall_intents"])
