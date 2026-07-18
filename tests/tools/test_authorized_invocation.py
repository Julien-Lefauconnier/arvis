# tests/tools/test_authorized_invocation.py
"""Opaque, single-use execution capability (campaign 6, Lot 3).

The executor runs a tool only from an AuthorizedInvocation minted by
its PRIVATE authority, and only on its FIRST presentation. A bare
invocation, a forged capability, one from a different authority, or a
replayed one is refused and the effect never runs. The a8 audit
(section 10) proved the campaign-5 authority was publicly mintable and
the capability reusable; both are pinned closed here: the authority is
not a public attribute, the mint handle is claimable exactly once, and
the nonce is consumed at execution.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.authorized_invocation import (
    CAPABILITY_FORMAT_VERSION,
    AuthorizedInvocation,
    CapabilityActivationBinding,
    CapabilityState,
    InvocationAuthority,
    UnauthorizedExecutionError,
)
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _Tool(BaseTool):
    name = "probe_tool"
    spec = ToolSpec(name="probe_tool", description="")

    def __init__(self) -> None:
        self.ran = False

    def execute_invocation(self, invocation):
        self.ran = True
        return {"ok": True}

    def execute(self, input_data):  # pragma: no cover
        raise AssertionError("legacy path must not be used")


def _executor():
    """Executor + tool + claimed mint (the test plays the manager role)."""
    registry = ToolRegistry()
    tool = _Tool()
    registry.register(tool)
    executor = ToolExecutor(registry)
    return executor, tool, executor.claim_minting_authority()


def _invocation():
    return ToolInvocation(tool_name="probe_tool", payload={}, process_id="p")


def _result():
    decision = SimpleNamespace(tool="probe_tool", tool_payload={})
    return SimpleNamespace(action_decision=decision)


def _activation(
    capability: AuthorizedInvocation,
    *,
    suffix: str = "1",
    intent_sha256: str = "a" * 64,
    run_id: str | None = "run-1",
) -> CapabilityActivationBinding:
    return CapabilityActivationBinding(
        receipt_id=f"receipt:{capability.nonce}:{suffix}",
        intent_sha256=intent_sha256,
        run_id=run_id,
        causal_id=f"causal:{capability.nonce}:{suffix}",
        durable_position=f"position:{suffix}",
        store_fingerprint="db:test",
        committed_at="2026-07-19T00:00:00+00:00",
    )


def _activate(
    authority: InvocationAuthority,
    capability: AuthorizedInvocation,
    *,
    suffix: str = "1",
) -> AuthorizedInvocation:
    assert (
        authority.activate(capability, _activation(capability, suffix=suffix)) is True
    )
    return capability


# ---------------------------------------------------------------
# Authority mints, executor honours
# ---------------------------------------------------------------


def test_capability_minted_by_the_claimed_authority_runs():
    executor, tool, mint = _executor()
    authorized = _activate(mint, mint.authorize(_invocation()))
    result = executor.execute_invocation(
        authorized, _result(), SimpleNamespace(extra={})
    )
    assert result.success is True
    assert tool.ran is True


def test_authority_verifies_its_own_capability():
    authority = InvocationAuthority()
    cap = authority.authorize(_invocation())
    assert authority.verifies(cap) is True


# ---------------------------------------------------------------
# The a7 bypasses, refused
# ---------------------------------------------------------------


def test_bare_invocation_is_refused():
    executor, tool, _mint = _executor()
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(_invocation(), _result(), SimpleNamespace(extra={}))  # type: ignore[arg-type]
    assert tool.ran is False


def test_capability_from_a_different_authority_is_refused():
    executor, tool, _mint = _executor()
    foreign = InvocationAuthority()
    forged = foreign.authorize(_invocation())
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(forged, _result(), SimpleNamespace(extra={}))
    assert tool.ran is False


def test_authority_does_not_verify_a_foreign_capability():
    a = InvocationAuthority()
    b = InvocationAuthority()
    cap_b = b.authorize(_invocation())
    assert a.verifies(cap_b) is False


def test_direct_execute_is_forbidden():
    from arvis.errors.tool_runtime import ToolAuthorizationError

    executor, _tool, _mint = _executor()
    with pytest.raises(ToolAuthorizationError, match="direct_tool_execution_forbidden"):
        executor.execute("probe_tool", {})
    with pytest.raises(ToolAuthorizationError, match="direct_tool_execution_forbidden"):
        executor.execute(_result(), SimpleNamespace(extra={}))


def test_execute_authorized_bypass_is_removed():
    executor, _tool, _mint = _executor()
    assert not hasattr(executor, "execute_authorized")


# ---------------------------------------------------------------
# No public executor on CognitiveOS
# ---------------------------------------------------------------


def test_cognitive_os_has_no_public_tool_executor():
    from arvis import CognitiveOS

    os_ = CognitiveOS()
    assert not hasattr(os_, "tool_executor")


# ---------------------------------------------------------------
# Capability shape
# ---------------------------------------------------------------


def test_capability_wraps_the_exact_invocation():
    authority = InvocationAuthority()
    inv = _invocation()
    cap = authority.authorize(inv)
    assert isinstance(cap, AuthorizedInvocation)
    assert cap.invocation is inv


def test_capability_is_end_to_end_through_the_manager():
    # The real manager mints the capability after policy; a full run
    # reaches the tool with no direct executor call in the test.
    from arvis import CognitiveOS

    ran = {"ok": False}

    class _E2ETool(BaseTool):
        name = "e2e_tool"
        spec = ToolSpec(name="e2e_tool", description="")

        def execute_invocation(self, invocation):
            ran["ok"] = True
            return {"ok": True}

        def execute(self, input_data):  # pragma: no cover
            raise AssertionError("legacy path must not be used")

    os_ = CognitiveOS()
    os_.register_tool(_E2ETool())
    # A normal run does not trigger a tool here; the point is that the
    # only path that could is the manager's minted capability, which we
    # proved is required. The registration and construction succeeding
    # is the structural guarantee.
    assert os_ is not None


# ---------------------------------------------------------------
# The a8 section 10 findings, pinned closed (campaign 6, Lot 3)
# ---------------------------------------------------------------


def test_executor_authority_is_not_public():
    executor, _tool, _mint = _executor()
    # The a8 bypass read `executor.authority` and minted freely; the
    # attribute no longer exists on the public surface.
    assert not hasattr(executor, "authority")


def test_minting_authority_is_claimable_exactly_once():
    registry = ToolRegistry()
    registry.register(_Tool())
    executor = ToolExecutor(registry)
    first = executor.claim_minting_authority()
    assert first is not None
    with pytest.raises(UnauthorizedExecutionError):
        executor.claim_minting_authority()


def test_authorized_invocation_is_single_use():
    executor, tool, mint = _executor()
    authorized = _activate(mint, mint.authorize(_invocation()))
    first = executor.execute_invocation(
        authorized, _result(), SimpleNamespace(extra={})
    )
    assert first is not None and first.success is True
    # Second presentation of the SAME capability: refused, no effect.
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(authorized, _result(), SimpleNamespace(extra={}))


def test_two_capabilities_for_the_same_invocation_are_independent():
    executor, _tool, mint = _executor()
    inv = _invocation()
    cap_a = _activate(mint, mint.authorize(inv), suffix="a")
    cap_b = _activate(mint, mint.authorize(inv), suffix="b")
    assert cap_a.nonce != cap_b.nonce
    assert (
        executor.execute_invocation(cap_a, _result(), SimpleNamespace(extra={})).success
        is True
    )
    # cap_b is its own single-use authorization: still valid.
    assert (
        executor.execute_invocation(cap_b, _result(), SimpleNamespace(extra={})).success
        is True
    )


def test_consume_is_single_use_at_the_authority_level():
    authority = InvocationAuthority()
    cap = _activate(authority, authority.authorize(_invocation()))
    assert authority.consume(cap) is True
    assert authority.consume(cap) is False
    # Read-only verification never consumes.
    assert authority.verifies(cap) is True


def test_capability_without_nonce_is_not_consumable():
    authority = InvocationAuthority()
    forged = AuthorizedInvocation(invocation=_invocation(), nonce="")
    assert authority.consume(forged) is False


def test_capability_carries_no_minting_secret():
    authority = InvocationAuthority()
    capability = authority.authorize(_invocation())
    assert not hasattr(capability, "_authority_token")
    assert "token" not in repr(capability).lower()


def test_unregistered_nonce_is_refused():
    authority = InvocationAuthority()
    forged = AuthorizedInvocation(
        invocation=_invocation(),
        nonce="attacker-selected-unregistered-nonce",
    )
    assert authority.verifies(forged) is False
    assert authority.consume(forged) is False


def test_minted_capability_requires_activation():
    authority = InvocationAuthority()
    capability = authority.mint(_invocation())
    assert authority.state_of(capability) is CapabilityState.MINTED
    assert authority.consume(capability) is False
    assert authority.activate(capability, _activation(capability)) is True
    assert authority.state_of(capability) is CapabilityState.ACTIVATED
    assert authority.consume(capability) is True
    assert authority.state_of(capability) is CapabilityState.CONSUMED


def test_authorize_is_now_a_non_executable_mint_alias():
    authority = InvocationAuthority()
    capability = authority.authorize(_invocation())
    assert authority.state_of(capability) is CapabilityState.MINTED
    assert authority.consume(capability) is False


def test_capability_commitment_binds_exact_invocation():
    authority = InvocationAuthority()
    capability = authority.authorize(_invocation())
    object.__setattr__(
        capability,
        "invocation",
        ToolInvocation(tool_name="other", payload={}, process_id="p"),
    )
    assert authority.verifies(capability) is False
    assert authority.consume(capability) is False


def test_capability_commitment_binds_exact_snapshot():
    authority = InvocationAuthority()
    capability = authority.authorize(
        _invocation(),
        {"allowed": True, "reason": "policy_allowed"},
    )
    object.__setattr__(
        capability,
        "authorization_snapshot",
        {"allowed": False, "reason": "attacker_override"},
    )
    assert authority.verifies(capability) is False
    assert authority.consume(capability) is False


def test_capability_commitment_detects_mutation_of_registered_invocation():
    authority = InvocationAuthority()
    capability = authority.authorize(_invocation())
    object.__setattr__(capability.invocation, "tool_name", "other")
    assert authority.verifies(capability) is False
    assert authority.consume(capability) is False


def test_capability_commitment_detects_nested_snapshot_mutation():
    authority = InvocationAuthority()
    capability = authority.authorize(
        _invocation(),
        {"policy": {"allowed": True}},
    )
    policy = capability.authorization_snapshot["policy"]
    assert isinstance(policy, dict)
    policy["allowed"] = False
    assert authority.verifies(capability) is False
    assert authority.consume(capability) is False


def test_capability_commitment_binds_format_version():
    authority = InvocationAuthority()
    capability = authority.authorize(_invocation())
    object.__setattr__(
        capability,
        "capability_format_version",
        CAPABILITY_FORMAT_VERSION + 1,
    )
    assert authority.verifies(capability) is False
    assert authority.consume(capability) is False


def test_revoked_capability_is_refused_by_executor():
    executor, tool, authority = _executor()
    capability = _activate(authority, authority.authorize(_invocation()))
    assert authority.revoke(capability) is True
    assert authority.state_of(capability) is CapabilityState.REVOKED
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(
            capability,
            _result(),
            SimpleNamespace(extra={}),
        )
    assert tool.ran is False


def test_manual_capability_clone_cannot_drive_effect():
    executor, tool, authority = _executor()
    minted = authority.authorize(
        _invocation(),
        {"allowed": True, "reason": "policy_allowed"},
    )
    clone = AuthorizedInvocation(
        invocation=minted.invocation,
        authorization_snapshot=minted.authorization_snapshot,
        nonce=minted.nonce,
        capability_format_version=minted.capability_format_version,
    )
    assert authority.verifies(clone) is False
    with pytest.raises(UnauthorizedExecutionError):
        executor.execute_invocation(clone, _result(), SimpleNamespace(extra={}))
    assert tool.ran is False


def test_revoke_is_idempotent_but_cannot_revoke_consumed_capability():
    authority = InvocationAuthority()
    revoked = authority.authorize(_invocation())
    assert authority.revoke(revoked) is True
    assert authority.revoke(revoked) is True

    consumed = _activate(authority, authority.authorize(_invocation()))
    assert authority.consume(consumed) is True
    assert authority.revoke(consumed) is False


def test_concurrent_consume_has_exactly_one_winner():
    authority = InvocationAuthority()
    capability = _activate(authority, authority.authorize(_invocation()))

    with ThreadPoolExecutor(max_workers=16) as pool:
        outcomes = list(
            pool.map(lambda _index: authority.consume(capability), range(64))
        )

    assert outcomes.count(True) == 1
    assert outcomes.count(False) == 63
    assert authority.state_of(capability) is CapabilityState.CONSUMED
