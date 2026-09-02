# tests/api/test_engine_run_as.py
"""ArvisEngine carries the production identity channel.

Campaign SURFACE (DM-S2, audit P1-7, 2026-09-02). PRODUCTION effect
syscalls require a host-attested ``AuthenticatedPrincipal``, but the
only entrypoint accepting one was ``CognitiveOS.run_as``: the
recommended facade (``ArvisEngine``) and the pinned host surface
offered no path to an authenticated run. ``ArvisEngine.run_as``
delegates to ``CognitiveOS.run_as`` with the same exact-type contract.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from arvis import ArvisEngine
from arvis.api.views.cognitive_result_view import CognitiveResultView
from arvis.kernel_core.access.models import AuthenticatedPrincipal, Principal


def _authenticated(user_id: str = "u1") -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        user_id=user_id,
        organization_id="org-1",
        authentication_source="oidc",
        authentication_strength="mfa",
        session_id_hash="sha256:session",
    )


def test_run_as_returns_a_public_view() -> None:
    engine = ArvisEngine()
    result = engine.run_as(_authenticated(), "hello")
    assert isinstance(result, CognitiveResultView)


def test_run_as_requires_an_exact_authenticated_principal() -> None:
    engine = ArvisEngine()
    with pytest.raises(TypeError):
        engine.run_as(Principal(user_id="u1"), "hello")  # type: ignore[arg-type]


def test_run_as_rejects_a_subclass_stamp() -> None:
    """The exact-type contract of CognitiveOS.run_as is preserved:
    a subclass is not an accepted stamp (no lookalike identities)."""

    class Lookalike(AuthenticatedPrincipal):
        pass

    lookalike = Lookalike(
        user_id="u1",
        organization_id="org-1",
        authentication_source="oidc",
        authentication_strength="mfa",
    )
    engine = ArvisEngine()
    with pytest.raises(TypeError):
        engine.run_as(lookalike, "hello")


def test_run_as_stamps_the_principal_on_the_trusted_channel() -> None:
    """Delegation reaches CognitiveOS.run_as: the exact principal
    instance lands on the pipeline context (same probe as the
    CognitiveOS-level test in test_production_effect_identity)."""
    principal = _authenticated()
    engine = ArvisEngine()
    captured: dict[str, object] = {}

    class _Runtime:
        def execute(self, ctx):  # noqa: ANN001, ANN202
            captured["ctx"] = ctx
            return SimpleNamespace(
                state=None,
                result=SimpleNamespace(
                    action_decision=None,
                    execution=SimpleNamespace(can_execute=False),
                ),
            )

    engine.os.runtime = _Runtime()
    result = engine.run_as(principal, "hello")
    assert result.decision is None
    ctx = captured["ctx"]
    assert getattr(ctx, "principal", None) is principal
    assert getattr(ctx, "user_id", None) == principal.user_id
