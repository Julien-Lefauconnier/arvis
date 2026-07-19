# arvis/kernel_core/canonicalization.py
"""Injective canonicalization of effect material (campaign 6, Lot 0).

The composed commitment, the pre-effect engagement digest and the tool
confirmations all reduce a real object to a canonical byte string, then
hash it. The a7 audit proved that reduction was lossy: distinct
business payloads collapsed to the same digest before SHA-256, so a
confirmation granted for one effect could authorize another. SHA-256
was never the problem; the transformation feeding it was. The a8 audit
then proved the campaign-5 encoder was still not injective on the
domain it declared: ``bytes``/``bytearray`` shared a tag, concrete path
types collapsed to their string, class identity ignored the module, and
underscore-prefixed operational state was silently dropped. This
revision closes that domain.

This module is the single injective encoder feeding every hash on the
effect path. Its contract:

- **Type-preserving.** ``bytes``, ``bytearray``, ``datetime``/``date``,
  ``UUID``, ``Decimal``, path types, ``Enum``, ``set``/``frozenset``,
  ``tuple``, dataclasses and objects are each mapped to a distinct,
  tagged canonical form. ``b"A"`` and ``bytearray(b"A")`` never
  coincide; ``Path("/a")`` and ``PurePath("/a")`` never coincide;
  ``{1: "x"}`` and ``{"1": "x"}`` never coincide.
- **Class identity is module-qualified.** Enums, dataclasses and plain
  objects bind ``module + qualname``, so two homonymous classes from
  different modules never share canonical material.
- **Envelope vs business payload.** Volatile per-run technical fields
  (wall-clock, random ids, ticks) are stripped ONLY from explicitly
  declared envelope structures, NEVER from business payloads. A
  business ``{"id": "record-A"}`` keeps its ``id``.
- **Injective on operationally significant differences.** Any two
  objects that differ in a way a host effect could act on produce
  different canonical bytes.
- **Fail-closed under REQUIRED, and fail-closed on hidden state.** A
  value with no canonical encoding is not silently reduced to a type
  marker: :func:`canonicalize` raises :class:`NonCanonicalizableError`.
  A plain object carrying underscore-prefixed attributes is REFUSED
  rather than partially encoded, because private state can be
  operational (``_endpoint``, ``_tenant``, ``_transaction``); the host
  either exposes the state publicly or provides an explicit serializer
  by defining ``__arvis_canonical__(self)`` on the class, whose return
  value (itself canonicalizable) becomes the bound representation,
  wrapped with the module-qualified class identity.
- **Finite floats only.** ``NaN`` compares unequal to itself, so no
  encoding of it can be injective; non-finite floats (``nan``,
  ``+/-inf``) are refused, as values and as dict keys. The officially
  injective domain is: ``None``, ``bool``, ``int``, finite ``float``,
  ``str``, ``bytes``, ``bytearray``, ``datetime``/``date``,
  ``Decimal``, ``UUID``, path types, ``Enum`` members, ``list``,
  ``tuple``, ``set``/``frozenset``, ``dict`` with scalar keys,
  dataclasses, plain objects with public-only state, and objects
  providing ``__arvis_canonical__``.
- **Deterministic across instances.** No ``repr`` of instances, no
  memory address, no wall-clock: the same logical object yields the
  same bytes in any process.

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
import math
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, Flag
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
# stable across versions by design. v2 (campaign 6): bytearray gets its
# own tag, paths and class identities are module-qualified, private
# attributes are refused instead of dropped, non-finite floats are
# refused, and the ``__arvis_canonical__`` serializer hook is honoured.
# v3 (campaign 8) dispatches enums before their scalar parents and gives
# enum mapping keys their own typed encoding.
CANONICALIZATION_VERSION = 3

# Reserved tag keys. A single-key dict whose sole key is one of these is
# a typed encoding, not a business dict; the encoder namespaces them so
# a business payload literally shaped like a tag is still distinguished
# (see _wrap / the collision note in the tests).
_TAG_BYTES = "__arvis_bytes_b64__"
_TAG_BYTEARRAY = "__arvis_bytearray_b64__"
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
        _TAG_BYTEARRAY,
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

# The host serializer hook. Looked up on the TYPE, never on the
# instance, so instance state cannot spoof the encoding path (an
# instance attribute of this name is underscore-prefixed anyway and
# would be refused by the private-state guard).
_SERIALIZER_HOOK = "__arvis_canonical__"

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


def _type_identity(cls: type) -> str:
    """Module-qualified class identity (campaign 6, closes 7.3).

    ``__qualname__`` alone let two homonymous classes from different
    modules share canonical material; binding ``module + qualname``
    keeps them distinct while staying deterministic across processes
    (both attributes are import-time constants, never memory-derived).
    """
    return f"{cls.__module__}.{cls.__qualname__}"


def _encode_key(key: Any, *, depth: int, path: str) -> str:
    """Encode a dict key preserving its type.

    ``str()``-flattening keys is exactly how ``{1: 'x'}`` and
    ``{'1': 'x'}`` collided in a7. A plain string key is emitted as-is
    (the common case, zero overhead and human-readable); any other key
    type is encoded as a typed token so the key type is part of the
    canonical bytes and cannot alias a string key.
    """
    if isinstance(key, Enum):
        # StrEnum and IntEnum inherit from their scalar value types. They
        # must be dispatched first, and their complete enum material is
        # embedded in the token so a member cannot alias its raw value.
        encoded = _canonicalize_enum(
            key,
            depth=depth + 1,
            path=f"{path}<key>",
        )
        return f"__arvis_key_enum__:{_stable_dumps(encoded)}"
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
        if not math.isfinite(key):
            raise NonCanonicalizableError(key, path=f"{path}<key>")
        return f"__arvis_key_float__:{key!r}"
    if key is None:
        return "__arvis_key_none__:"
    if isinstance(key, bytes):
        token = base64.b64encode(key).decode("ascii")
        return f"__arvis_key_bytes__:{token}"
    raise NonCanonicalizableError(key, path=f"{path}<key>")


def _wrap(tag: str, value: JSONValue) -> dict[str, JSONValue]:
    return {tag: value}


def _canonicalize_enum(obj: Enum, *, depth: int, path: str) -> JSONValue:
    """Encode a member with type, name, value and flag decomposition."""
    material: dict[str, JSONValue] = {
        "enum": _type_identity(type(obj)),
        "name": obj.name,
        "value": _canonicalize(
            obj.value,
            depth=depth + 1,
            path=f"{path}<value>",
        ),
    }
    if isinstance(obj, Flag):
        # Iteration yields canonical single-bit members. The exact raw value
        # above also binds unnamed/unknown bits; this ordered decomposition
        # makes composite Flag/IntFlag semantics explicit.
        material["flag_members"] = [
            {
                "name": member.name,
                "value": _canonicalize(
                    member.value,
                    depth=depth + 1,
                    path=f"{path}<flag:{member.name}>",
                ),
            }
            for member in type(obj)
            if member.name is not None and member in obj
        ]
    return _wrap(_TAG_ENUM, material)


def _canonicalize(obj: Any, *, depth: int, path: str) -> JSONValue:
    if depth > _MAX_DEPTH:
        raise NonCanonicalizableError(obj, path=f"{path} (max depth exceeded)")

    # Enum must precede str/int: StrEnum, IntEnum and IntFlag inherit from
    # those scalar parents and otherwise collapse to their raw values.
    if isinstance(obj, Enum):
        return _canonicalize_enum(obj, depth=depth, path=path)

    # --- JSON scalars pass through, with the bool/int subtlety ---
    if obj is None or isinstance(obj, str):
        return obj
    if isinstance(obj, bool):
        # bool is an int subclass; keep it distinct from 0/1.
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        # NaN is unequal to itself: no encoding of it can be injective.
        # Non-finite floats are outside the declared domain (fail-closed
        # rather than emitting non-strict JSON tokens).
        if not math.isfinite(obj):
            raise NonCanonicalizableError(obj, path=path)
        return obj

    # --- typed scalars: each to a distinct tagged form ---
    if isinstance(obj, bytes):
        return _wrap(_TAG_BYTES, base64.b64encode(obj).decode("ascii"))
    if isinstance(obj, bytearray):
        # Own tag (campaign 6, closes 7.1): bytes is immutable,
        # bytearray is mutable, and adapters may treat them differently;
        # equal content must not alias across the two types.
        return _wrap(_TAG_BYTEARRAY, base64.b64encode(bytes(obj)).decode("ascii"))
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
        # Concrete path type bound with the value (campaign 6, closes
        # 7.2): Path("/a") and PurePath("/a") render the same string but
        # are not interchangeable for a host effect.
        return _wrap(
            _TAG_PATH,
            {"type": _type_identity(type(obj)), "path": str(obj)},
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

    # --- host serializer hook: explicit contract for private state ---
    hook = getattr(type(obj), _SERIALIZER_HOOK, None)
    if callable(hook):
        serialized = hook(obj)
        return _wrap(
            _TAG_OBJECT,
            {
                "type": _type_identity(type(obj)),
                # Distinct key from "fields": a serializer output can
                # never alias an attribute encoding of the same class.
                "serialized": _canonicalize(
                    serialized, depth=depth + 1, path=f"{path}<serialized>"
                ),
            },
        )

    # --- dataclasses and plain objects: attributes, injectively ---
    if is_dataclass(obj) and not isinstance(obj, type):
        attrs = {f.name: getattr(obj, f.name, None) for f in fields(obj)}
        return _wrap(
            _TAG_OBJECT,
            {
                "type": _type_identity(type(obj)),
                "fields": _canonicalize_dict(attrs, depth=depth, path=path),
            },
        )
    obj_dict = _object_attributes(obj, path=path)
    if obj_dict is not None:
        return _wrap(
            _TAG_OBJECT,
            {
                "type": _type_identity(type(obj)),
                "fields": _canonicalize_dict(obj_dict, depth=depth, path=path),
            },
        )

    # No injective encoding: refuse rather than alias (fail-closed).
    raise NonCanonicalizableError(obj, path=path)


def _object_attributes(obj: Any, *, path: str) -> dict[str, Any] | None:
    """Full attribute map of a plain object, or None if it has none.

    Uses ``__dict__`` when present. Underscore-prefixed attributes are
    REFUSED, not dropped (campaign 6, closes 7.4): private state can be
    operational (``_endpoint``, ``_resource_id``, ``_tenant``), and an
    encoding that ignores it lets two operationally different objects
    share a commitment. A class holding private state either exposes it
    publicly or declares an explicit ``__arvis_canonical__`` serializer.
    """
    try:
        raw = vars(obj)
    except TypeError:
        return None
    for key in raw:
        if str(key).startswith("_"):
            raise NonCanonicalizableError(
                obj,
                path=f"{path} (private attribute {key!r}; expose it or "
                f"define {_SERIALIZER_HOOK})",
            )
    return dict(raw)


def _canonicalize_dict(
    obj: dict[Any, Any], *, depth: int, path: str
) -> dict[str, JSONValue]:
    # A business dict whose ONLY key is a reserved tag is escaped, so it
    # can never be read back as a typed encoding (tag ambiguity guard).
    if len(obj) == 1:
        (only_key,) = obj.keys()
        if type(only_key) is str and only_key in _RESERVED_TAGS:
            inner = _canonicalize(
                obj[only_key], depth=depth + 1, path=f"{path}.{only_key}"
            )
            return {_TAG_LITERAL: {only_key: inner}}

    out: dict[str, JSONValue] = {}
    # Detect key-type collisions after encoding: if two distinct keys
    # encode to the same token, refuse (should not happen with the
    # typed scheme, but never alias silently).
    for key, value in obj.items():
        enc_key = _encode_key(key, depth=depth, path=path)
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
    type, set membership, object field, concrete path type, private
    state exposed via serializer) yields a different hash.
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
