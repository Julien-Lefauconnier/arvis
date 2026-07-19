# arvis/kernel_core/access/identity.py

from __future__ import annotations

from arvis.kernel_core.access.models import AuthenticatedPrincipal, Principal

CONTEXT_PRINCIPAL_ATTR = "principal"


def principal_from_context(ctx: object) -> Principal | None:
    """Read the authenticated principal carried on the execution context.

    Identity travels as ambient process state on the context, stamped by the
    realization layer at the start of a run, not as a per-syscall operational
    argument. This separates the trusted identity channel (the context, set
    from an authenticated session) from the operational parameter channel (the
    syscall arguments, which may be influenced by cognition downstream of the
    Gate).

    The carried identity is a trusted input: ARVIS does not authenticate it and
    never derives it from cognition. Returns ``None`` when no valid principal is
    present, so callers fall back to a bare, user-scoped principal, which is
    behaviour-neutral.
    """
    principal = getattr(ctx, CONTEXT_PRINCIPAL_ATTR, None)
    if isinstance(principal, Principal):
        return principal
    return None


def authenticated_principal_from_context(
    ctx: object,
) -> AuthenticatedPrincipal | None:
    """Return the exact host-authenticated principal carried by ``ctx``."""
    principal = principal_from_context(ctx)
    if type(principal) is AuthenticatedPrincipal:
        return principal
    return None
