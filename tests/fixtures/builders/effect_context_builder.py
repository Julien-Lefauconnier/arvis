from __future__ import annotations

from arvis.tools.effect_context import AuthorizedEffectContext


def build_effect_context(
    *,
    principal: str = "u1",
    tenant: str | None = None,
    authentication_source: str = "test",
    authentication_strength: str = "unattested",
    service_id: str | None = None,
    session_id_hash: str | None = None,
    process_id: str = "p",
    run_id: str | None = None,
    host_binding_commitment: str | None = None,
) -> AuthorizedEffectContext:
    return AuthorizedEffectContext(
        principal=principal,
        tenant=tenant,
        authentication_source=authentication_source,
        authentication_strength=authentication_strength,
        service_id=service_id,
        session_id_hash=session_id_hash,
        process_id=process_id,
        run_id=run_id,
        host_binding_commitment=host_binding_commitment,
    )
