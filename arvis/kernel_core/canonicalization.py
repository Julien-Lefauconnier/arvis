# arvis/kernel_core/canonicalization.py
"""Injective canonicalization of effect material (campaign 5, Lot 0).

The composed commitment, the pre-effect engagement digest and the tool
confirmations all reduce a real object to a canonical byte string, then
hash it. The a7 audit proved that reduction was lossy: distinct
business payloads collapsed to the same digest before SHA-256, so a
confirmation granted for one effect could authorize another. SHA-256
was never the problem; the transformation feeding it was.

This module is the single injective encoder feeding every hash on the
effect path. Its contract:

- **Type-preserving.** ``bytes``, ``datetime``/``date``, ``UUID``,
  ``Decimal``, ``Path``, ``Enum``, ``set``/``frozenset``, ``tuple``,
  dataclasses and objects are each mapped to a distinct, tagged
  canonical form. ``b"A"`` and ``b"B"`` never coincide; ``{1: "x"}``
  and ``{"1": "x"}`` never coincide (the key type is encoded, not
  ``str()``-flattened).
- **Envelope vs business payload.** Volatile per-run technical fields
  (wall-clock, random ids, ticks) are stripped ONLY from explicitly
  declared envelope structures, NEVER from business payloads. A
  business ``{"id": "record-A"}`` keeps its ``id``.
- **Injective on operationally significant differences.** Any two
  objects that differ in a way a host effect could act on produce
  different canonical bytes.
- **Fail-closed under REQUIRED.** A value with no canonical encoding is
  not silently reduced to a type marker: :func:`canonicalize` raises
  :class:`NonCanonicalizableError`. The caller decides whether that
  makes the commitment unavailable (REQUIRED) or degraded (DEGRADED).
- **Deterministic across instances.** No ``repr``, no memory address,
  no wall-clock: the same logical object yields the same bytes in any
  process (the campaign-4 ``decided_at`` trap does not recur here).

The redaction step (replacing content-bearing values by their hash for
ZK) is layered ON TOP of this encoder by :mod:`arvis.kernel_core.
syscalls.engagement`, not here: canonicalization answers "are these two
objects the same effect", redaction answers "what may cross the ZK
boundary". Keeping them separate is what lets redaction stay lossy (by
design) while canonicalization stays injective (by contract).
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any, TypeAlias
from uuid import UUID

# The canonical JSON value space. Every encoder output is one of these;
# JSONValue is the closed set json.dumps serializes deterministically.
JSONValue: TypeAlias = (
    None | bool | int | float | str | list["JSONValue"] | dict[str, "JSONValue"]
)

# Canonicalization format version. Any change to the encoding of any
# type, to the envelope key set, or to the key-type encoding is a bump
# here and, downstream, a bump of REDACTION_POLICY_VERSION,
# COMMITMENT_VERSION and the confirmation format version. Hashes are not
# stable across versions by design.
CANONICALIZATION_VERSION = 1

# Reserved tag keys. A single-key dict whose sole key is one of these is
# a typed encoding, not a business dict; the encoder namespaces them so
# a business payload literally shaped like a tag is still distinguished
# (see _wrap / the collision note in the tests).
_TAG_BYTES = "__arvis_bytes_b64__"
_TAG_DATETIME = "__arvis_datetime__"
_TAG_DATE = "__arvis_date__"
_TAG_DECIMAL = "__arvis_decimal__"
_TAG_UUID = "__arvis_uuid__"
_TAG_PATH = "__arvis_path__"
_TAG_ENUM = "__arvis_enum__"
_TAG_SET = "__arvis_set__"
_TAG_FROZENSET = "__arvis_frozenset__"
_TAG_TUPLE = "__arvis_tuple__"
_TAG_OBJECT = "__arvis_object__"
_TAG_KEYED = "__arvis_keyed__"
# A business dict that happens to use a reserved tag as its only key is
# escaped under this wrapper so it can never be read back as a typed
# encoding.
_TAG_LITERAL = "__arvis_literal__"

_RESERVED_TAGS: frozenset[str] = frozenset(
    {
        _TAG_BYTES,
        _TAG_DATETIME,
        _TAG_DATE,
        _TAG_DECIMAL,
        _TAG_UUID,
        _TAG_PATH,
        _TAG_ENUM,
        _TAG_SET,
        _TAG_FROZENSET,
        _TAG_TUPLE,
        _TAG_OBJECT,
        _TAG_KEYED,
        _TAG_LITERAL,
    }
)

# Depth cap: a guard against pathological nesting, not a lossy fallback.
# Reaching it raises rather than collapsing to type identity, so two
# deep-but-distinct objects never coincide silently.
_MAX_DEPTH = 64


class NonCanonicalizableError(TypeError):
    """A value has no injective canonical encoding.

    Raised instead of collapsing the value to a type marker: under a
    REQUIRED audit policy the caller turns this into an unavailable
    commitment (reason ``non_canonicalizable``); under DEGRADED it
    flags. Never swallowed inside this module.
    """

    def __init__(self, value: Any, *, path: str) -> None:
        self.python_type = type(value).__qualname__
        self.path = path
        super().__init__(
            f"no canonical encoding for value of type {self.python_type!r} "
            f"at {path} (a REQUIRED commitment cannot bind an object it "
            f"cannot distinguish; provide a host serializer or exclude it)"
        )


def _encode_key(key: Any, *, path: str) -> str:
    """Encode a dict key preserving its type.

    ``str()``-flattening keys is exactly how ``{1: 'x'}`` and
    ``{'1': 'x'}`` collided in a7. A plain string key is emitted as-is
    (the common case, zero overhead and human-readable); any other key
    type is encoded as a typed token so the key type is part of the
    canonical bytes and cannot alias a string key.
    """
    if isinstance(key, str):
        # A string that could be mistaken for a typed token is escaped.
        if key.startswith("__arvis_key_"):
            return f"__arvis_key_str__:{key}"
        return key
    if isinstance(key, bool):
        return f"__arvis_key_bool__:{key}"
    if isinstance(key, int):
        return f"__arvis_key_int__:{key}"
    if isinstance(key, float):
        return f"__arvis_key_float__:{key!r}"
    if key is None:
        return "__arvis_key_none__:"
    if isinstance(key, bytes):
        token = base64.b64encode(key).decode("ascii")
        return f"__arvis_key_bytes__:{token}"
    raise NonCanonicalizableError(key, path=f"{path}<key>")


def _wrap(tag: str, value: JSONValue) -> dict[str, JSONValue]:
    return {tag: value}


def _canonicalize(obj: Any, *, depth: int, path: str) -> JSONValue:
    if depth > _MAX_DEPTH:
        raise NonCanonicalizableError(obj, path=f"{path} (max depth exceeded)")

    # --- JSON scalars pass through, with the bool/int subtlety ---
    if obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, bool):
        # bool is an int subclass; keep it distinct from 0/1.
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        return obj

    # --- typed scalars: each to a distinct tagged form ---
    if isinstance(obj, bytes):
        return _wrap(_TAG_BYTES, base64.b64encode(obj).decode("ascii"))
    if isinstance(obj, bytearray):
        return _wrap(_TAG_BYTES, base64.b64encode(bytes(obj)).decode("ascii"))
    if isinstance(obj, datetime):
        # Explicit tz marker so naive and aware never alias; isoformat
        # preserves microseconds and offset.
        return _wrap(
            _TAG_DATETIME,
            {"iso": obj.isoformat(), "tz": obj.tzinfo is not None},
        )
    if isinstance(obj, date):
        return _wrap(_TAG_DATE, obj.isoformat())
    if isinstance(obj, Decimal):
        # str(Decimal) is exact and preserves trailing zeros /
        # exponent, unlike float; "12.3400" != "12.34".
        return _wrap(_TAG_DECIMAL, str(obj))
    if isinstance(obj, UUID):
        return _wrap(_TAG_UUID, str(obj))
    if isinstance(obj, PurePath):
        return _wrap(_TAG_PATH, str(obj))
    if isinstance(obj, Enum):
        # Bind the member identity (class + name), not just the value:
        # two enums sharing a value stay distinct.
        return _wrap(
            _TAG_ENUM,
            {"enum": type(obj).__qualname__, "name": obj.name},
        )

    # --- containers ---
    if isinstance(obj, dict):
        return _canonicalize_dict(obj, depth=depth, path=path)
    if isinstance(obj, tuple):
        return _wrap(
            _TAG_TUPLE,
            [
                _canonicalize(v, depth=depth + 1, path=f"{path}[{i}]")
                for i, v in enumerate(obj)
            ],
        )
    if isinstance(obj, (set, frozenset)):
        # Order-independent: canonicalize each element, then sort by the
        # element's own canonical bytes so {a, b} == {b, a}.
        encoded = [_canonicalize(v, depth=depth + 1, path=f"{path}{{}}") for v in obj]
        encoded.sort(key=_stable_dumps)
        tag = _TAG_FROZENSET if isinstance(obj, frozenset) else _TAG_SET
        return _wrap(tag, encoded)
    if isinstance(obj, (list,)):
        return [
            _canonicalize(v, depth=depth + 1, path=f"{path}[{i}]")
            for i, v in enumerate(obj)
        ]

    # --- dataclasses and plain objects: attributes, injectively ---
    if is_dataclass(obj) and not isinstance(obj, type):
        attrs = {f.name: getattr(obj, f.name, None) for f in fields(obj)}
        return _wrap(
            _TAG_OBJECT,
            {
                "type": type(obj).__qualname__,
                "fields": _canonicalize_dict(attrs, depth=depth, path=path),
            },
        )
    obj_dict = _object_attributes(obj, path=path)
    if obj_dict is not None:
        return _wrap(
            _TAG_OBJECT,
            {
                "type": type(obj).__qualname__,
                "fields": _canonicalize_dict(obj_dict, depth=depth, path=path),
            },
        )

    # No injective encoding: refuse rather than alias (fail-closed).
    raise NonCanonicalizableError(obj, path=path)


def _object_attributes(obj: Any, *, path: str) -> dict[str, Any] | None:
    """Public attribute map of a plain object, or None if it has none.

    Uses ``__dict__`` when present. Underscore-prefixed attributes are
    excluded as implementation detail (consistent with the a7 material
    builder), so the encoding binds the object's declared state.
    """
    try:
        raw = vars(obj)
    except TypeError:
        return None
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def _canonicalize_dict(
    obj: dict[Any, Any], *, depth: int, path: str
) -> dict[str, JSONValue]:
    # A business dict whose ONLY key is a reserved tag is escaped, so it
    # can never be read back as a typed encoding (tag ambiguity guard).
    if len(obj) == 1:
        (only_key,) = obj.keys()
        if isinstance(only_key, str) and only_key in _RESERVED_TAGS:
            inner = _canonicalize(
                obj[only_key], depth=depth + 1, path=f"{path}.{only_key}"
            )
            return {_TAG_LITERAL: {only_key: inner}}

    out: dict[str, JSONValue] = {}
    # Detect key-type collisions after encoding: if two distinct keys
    # encode to the same token, refuse (should not happen with the
    # typed scheme, but never alias silently).
    for key, value in obj.items():
        enc_key = _encode_key(key, path=path)
        if enc_key in out:
            raise NonCanonicalizableError(
                obj, path=f"{path} (key token collision on {enc_key!r})"
            )
        out[enc_key] = _canonicalize(value, depth=depth + 1, path=f"{path}.{enc_key}")
    return out


def _stable_dumps(obj: JSONValue) -> str:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def canonicalize(obj: Any) -> JSONValue:
    """Injective canonical JSON value for an effect object.

    Type-preserving, envelope-free (the caller strips envelopes before
    calling), deterministic across instances. Raises
    :class:`NonCanonicalizableError` on any value with no injective
    encoding rather than aliasing it.
    """
    return _canonicalize(obj, depth=0, path="$")


def canonical_bytes(obj: Any) -> bytes:
    """Canonical UTF-8 byte string of an effect object."""
    return _stable_dumps(canonicalize(obj)).encode("utf-8")


def canonical_hash(obj: Any) -> str:
    """Deterministic SHA-256 hex of the injective canonical form.

    This is the single hash primitive on the effect path. Two objects
    hash equal iff they are the same effect; any operationally
    significant difference (business id, timestamp, bytes content, key
    type, set membership, object field) yields a different hash.
    """
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


__all__ = [
    "CANONICALIZATION_VERSION",
    "JSONValue",
    "NonCanonicalizableError",
    "canonical_bytes",
    "canonical_hash",
    "canonicalize",
]
