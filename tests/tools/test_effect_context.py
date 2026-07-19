"""Immutable authorized effect-context contract (campaign 8, Lot 1)."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace

import pytest

from arvis.kernel_core.canonicalization import canonical_hash
from arvis.tools.effect_context import (
    EFFECT_CONTEXT_FORMAT_VERSION,
    AuthorizedEffectContext,
)


def _context(**changes: object) -> AuthorizedEffectContext:
    values: dict[str, object] = {
        "principal": "alice",
        "tenant": "tenant-a",
        "authentication_source": "oidc",
        "authentication_strength": "mfa",
        "service_id": "document-service",
        "session_id_hash": "sha256:session-a",
        "process_id": "proc::alice::0",
        "run_id": "run-a",
        "host_binding_commitment": "a" * 64,
    }
    values.update(changes)
    return AuthorizedEffectContext(**values)  # type: ignore[arg-type]


def test_effect_context_material_is_complete_and_versioned() -> None:
    context = _context()

    assert context.to_material() == {
        "effect_context_format_version": EFFECT_CONTEXT_FORMAT_VERSION,
        "principal": "alice",
        "tenant": "tenant-a",
        "authentication_source": "oidc",
        "authentication_strength": "mfa",
        "service_id": "document-service",
        "session_id_hash": "sha256:session-a",
        "process_id": "proc::alice::0",
        "run_id": "run-a",
        "host_binding_commitment": "a" * 64,
    }


def test_effect_context_is_frozen_and_has_no_dynamic_attribute_store() -> None:
    context = _context()

    with pytest.raises(FrozenInstanceError):
        context.principal = "bob"  # type: ignore[misc]
    assert not hasattr(context, "__dict__")
    assert not hasattr(context, "context")
    assert not hasattr(context, "credentials")
    assert not hasattr(context, "services")


@pytest.mark.parametrize(
    "field_name",
    (
        "principal",
        "authentication_source",
        "authentication_strength",
        "process_id",
    ),
)
@pytest.mark.parametrize("invalid", ("", None, 1))
def test_required_effect_context_fields_refuse_invalid_values(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _context(**{field_name: invalid})


@pytest.mark.parametrize(
    "field_name",
    (
        "tenant",
        "service_id",
        "session_id_hash",
        "run_id",
        "host_binding_commitment",
    ),
)
@pytest.mark.parametrize("invalid", ("", 1))
def test_optional_effect_context_fields_refuse_invalid_values(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(ValueError, match=field_name):
        _context(**{field_name: invalid})


def test_optional_effect_context_fields_accept_none() -> None:
    context = _context(
        tenant=None,
        service_id=None,
        session_id_hash=None,
        run_id=None,
        host_binding_commitment=None,
    )

    assert context.tenant is None
    assert context.service_id is None
    assert context.session_id_hash is None
    assert context.run_id is None
    assert context.host_binding_commitment is None


@pytest.mark.parametrize("invalid_version", (True, 0, 2, "1"))
def test_effect_context_refuses_unknown_or_invalid_versions(
    invalid_version: object,
) -> None:
    with pytest.raises(ValueError, match="unsupported effect context format version"):
        _context(format_version=invalid_version)


def test_equivalent_effect_contexts_have_the_same_commitment() -> None:
    first = _context()
    second = _context()

    assert first is not second
    assert first.commitment_sha256 == second.commitment_sha256
    assert first.commitment_sha256 == canonical_hash(first.to_material())


@pytest.mark.parametrize(
    ("field_name", "changed_value"),
    (
        ("principal", "bob"),
        ("tenant", "tenant-b"),
        ("authentication_source", "mtls"),
        ("authentication_strength", "hardware-key"),
        ("service_id", "mail-service"),
        ("session_id_hash", "sha256:session-b"),
        ("process_id", "proc::alice::1"),
        ("run_id", "run-b"),
        ("host_binding_commitment", "b" * 64),
    ),
)
def test_each_effect_context_field_changes_the_commitment(
    field_name: str,
    changed_value: str,
) -> None:
    original = _context()
    changed = replace(original, **{field_name: changed_value})

    assert changed.commitment_sha256 != original.commitment_sha256


def test_effect_context_itself_is_canonicalizable() -> None:
    context = _context()

    assert canonical_hash(context)
