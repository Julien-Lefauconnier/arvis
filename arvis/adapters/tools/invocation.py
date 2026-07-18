"""Immutable tool invocation material.

Campaign 7 closes the payload TOCTOU left by a frozen ``ToolInvocation``
containing a mutable dictionary. The invocation now owns a
:class:`FrozenEffectPayload`: a defensive, canonical snapshot created at
authorization time. Every consumer receives a fresh materialization, so
policy, validation, audit and execution never share a mutable reference
with the host or with each other.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any
from uuid import UUID

from arvis.kernel_core.canonicalization import canonical_bytes as encode_canonical_bytes


class FrozenEffectPayloadError(TypeError):
    """A tool payload cannot be isolated into canonical effect material."""


class FrozenEffectPayloadIntegrityError(RuntimeError):
    """The private payload snapshot no longer matches its canonical bytes."""


_IMMUTABLE_LEAF_TYPES = (
    type(None),
    bool,
    int,
    float,
    str,
    bytes,
    date,
    datetime,
    Decimal,
    UUID,
    PurePath,
    Enum,
)


def _mutable_object_ids(value: Any, *, seen: set[int] | None = None) -> set[int]:
    """Return identities that must not be shared across payload copies.

    ``copy.deepcopy`` is intentionally verified instead of trusted: a host
    object may implement ``__deepcopy__`` incorrectly and return itself or
    retain mutable children. Known immutable leaves may be shared; mutable
    containers, dataclasses and ordinary objects may not.
    """
    if isinstance(value, _IMMUTABLE_LEAF_TYPES):
        return set()

    if seen is None:
        seen = set()
    object_id = id(value)
    if object_id in seen:
        return set()
    seen.add(object_id)

    mutable_ids: set[int] = set()

    if isinstance(value, tuple | frozenset):
        for item in value:
            mutable_ids.update(_mutable_object_ids(item, seen=seen))
        return mutable_ids

    mutable_ids.add(object_id)

    if isinstance(value, dict):
        for key, item in value.items():
            mutable_ids.update(_mutable_object_ids(key, seen=seen))
            mutable_ids.update(_mutable_object_ids(item, seen=seen))
        return mutable_ids

    if isinstance(value, list | set):
        for item in value:
            mutable_ids.update(_mutable_object_ids(item, seen=seen))
        return mutable_ids

    if isinstance(value, bytearray):
        return mutable_ids

    if is_dataclass(value) and not isinstance(value, type):
        for dataclass_field in fields(value):
            mutable_ids.update(
                _mutable_object_ids(
                    getattr(value, dataclass_field.name),
                    seen=seen,
                )
            )
        return mutable_ids

    try:
        attributes = vars(value)
    except TypeError:
        return mutable_ids

    for item in attributes.values():
        mutable_ids.update(_mutable_object_ids(item, seen=seen))
    return mutable_ids


def _assert_isolated(source: Any, clone: Any) -> None:
    shared = _mutable_object_ids(source) & _mutable_object_ids(clone)
    if shared:
        raise FrozenEffectPayloadError(
            "tool payload deepcopy retained mutable references; effect material "
            "must be fully isolated"
        )


class FrozenEffectPayload:
    """Canonical, immutable snapshot of one tool payload.

    The canonical bytes and their SHA-256 are public immutable metadata.
    The material snapshot is private and never returned directly. A fresh
    deep copy is produced for every consumer and checked against the bytes
    captured at freeze time; any internal corruption therefore fails closed
    before the tool body is entered.
    """

    __slots__ = ("__canonical_bytes", "__sha256", "__snapshot")

    __canonical_bytes: bytes
    __sha256: str
    __snapshot: dict[str, Any]

    def __init__(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            raise FrozenEffectPayloadError("tool payload must be a dictionary")

        try:
            snapshot: dict[str, Any] = copy.deepcopy(payload)
        except Exception as exc:
            raise FrozenEffectPayloadError(
                "tool payload could not be defensively copied"
            ) from exc

        _assert_isolated(payload, snapshot)
        encoded = encode_canonical_bytes(snapshot)

        object.__setattr__(self, "_FrozenEffectPayload__snapshot", snapshot)
        object.__setattr__(self, "_FrozenEffectPayload__canonical_bytes", encoded)
        object.__setattr__(
            self,
            "_FrozenEffectPayload__sha256",
            hashlib.sha256(encoded).hexdigest(),
        )

    def __setattr__(self, name: str, value: Any) -> None:
        del name, value
        raise AttributeError("FrozenEffectPayload is immutable")

    @property
    def canonical_bytes(self) -> bytes:
        """Exact canonical material captured at authorization time."""
        return self.__canonical_bytes

    @property
    def sha256(self) -> str:
        """SHA-256 of :attr:`canonical_bytes`."""
        return self.__sha256

    def materialize(self) -> dict[str, Any]:
        """Return a fresh isolated payload matching the frozen commitment."""
        try:
            materialized: dict[str, Any] = copy.deepcopy(self.__snapshot)
        except Exception as exc:
            raise FrozenEffectPayloadIntegrityError(
                "frozen tool payload could not be materialized"
            ) from exc

        try:
            _assert_isolated(self.__snapshot, materialized)
        except FrozenEffectPayloadError as exc:
            raise FrozenEffectPayloadIntegrityError(str(exc)) from exc

        if encode_canonical_bytes(materialized) != self.__canonical_bytes:
            raise FrozenEffectPayloadIntegrityError(
                "frozen tool payload no longer matches its canonical material"
            )
        return materialized

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FrozenEffectPayload):
            return NotImplemented
        return self.__canonical_bytes == other.__canonical_bytes

    def __hash__(self) -> int:
        return hash(self.__canonical_bytes)

    def __repr__(self) -> str:
        return f"FrozenEffectPayload(sha256={self.__sha256!r})"


@dataclass(frozen=True, slots=True, init=False)
class ToolInvocation:
    """One fully contextualized tool invocation with frozen effect material."""

    tool_name: str
    _effect_payload: FrozenEffectPayload = field(repr=False)

    # runtime context (minimal & controlled)
    process_id: str
    user_id: str | None = None

    # governance
    # risk_score is the real risk of the turn (hardening composition of
    # the declared input risk and the assessed collapse risk), wired by
    # the tool manager; 0.0 only when no signal is available.
    risk_score: float = 0.0
    audit_required: bool = False

    # F-006-a5: complete invocation context (skeleton). Opaque to
    # arvis; the host assigns meaning (same doctrine as capability
    # grants). principal and tenant are threaded from the trusted
    # context identity channel when a Principal is stamped;
    # consent_granted is reserved for a host composition channel and
    # stays empty until one exists.
    principal: str | None = None
    tenant: str | None = None
    consent_granted: tuple[str, ...] = ()

    # P1-10-a6 (decision D4-d): bound confirmation. Set by the tool
    # manager after consuming a registry record that matches this exact
    # invocation (tool, canonical payload hash, principal, tenant);
    # never derived from request-facing extra.
    confirmed: bool = False
    confirmation_id: str | None = None
    confirmation_commitment: str | None = None

    # execution semantics
    idempotency_key: str | None = None
    context: Any | None = None

    def __init__(
        self,
        tool_name: str,
        payload: dict[str, Any] | FrozenEffectPayload,
        process_id: str,
        user_id: str | None = None,
        risk_score: float = 0.0,
        audit_required: bool = False,
        principal: str | None = None,
        tenant: str | None = None,
        consent_granted: tuple[str, ...] = (),
        confirmed: bool = False,
        confirmation_id: str | None = None,
        confirmation_commitment: str | None = None,
        idempotency_key: str | None = None,
        context: Any | None = None,
    ) -> None:
        frozen_payload = (
            payload
            if isinstance(payload, FrozenEffectPayload)
            else FrozenEffectPayload(payload)
        )
        object.__setattr__(self, "tool_name", tool_name)
        object.__setattr__(self, "_effect_payload", frozen_payload)
        object.__setattr__(self, "process_id", process_id)
        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "risk_score", risk_score)
        object.__setattr__(self, "audit_required", audit_required)
        object.__setattr__(self, "principal", principal)
        object.__setattr__(self, "tenant", tenant)
        object.__setattr__(self, "consent_granted", consent_granted)
        object.__setattr__(self, "confirmed", confirmed)
        object.__setattr__(self, "confirmation_id", confirmation_id)
        object.__setattr__(self, "confirmation_commitment", confirmation_commitment)
        object.__setattr__(self, "idempotency_key", idempotency_key)
        object.__setattr__(self, "context", context)

    @property
    def payload(self) -> dict[str, Any]:
        """Fresh execution-safe copy of the authorized payload."""
        return self._effect_payload.materialize()

    @property
    def frozen_payload(self) -> FrozenEffectPayload:
        """Immutable canonical payload owned by this invocation."""
        return self._effect_payload

    @property
    def payload_sha256(self) -> str:
        """Canonical payload hash captured before authorization."""
        return self._effect_payload.sha256

    @property
    def canonical_payload_bytes(self) -> bytes:
        """Canonical payload bytes captured before authorization."""
        return self._effect_payload.canonical_bytes

    def materialize_payload(self) -> dict[str, Any]:
        """Explicit payload materialization for validation or execution."""
        return self._effect_payload.materialize()


__all__ = [
    "FrozenEffectPayload",
    "FrozenEffectPayloadError",
    "FrozenEffectPayloadIntegrityError",
    "ToolInvocation",
]
