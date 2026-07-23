"""A subclass of a native type is not its parent.

Canonicalization dispatched on ``isinstance``, so ``UserId("alice")`` and
``"alice"`` produced the same bytes. That is not cosmetic: commitments and
confirmations are keyed on canonical bytes, so a confirmation minted for a
typed payload could be redeemed with the plain-string one.

Encoding such a subclass as a plain object is not an answer either. A str or
int subclass has an empty ``__dict__``, so the attribute fallback would make
``UserId("alice")`` and ``UserId("bob")`` collide with each other, which is
worse than the defect it replaces. A subclass therefore either declares
``__arvis_canonical__``, or is refused.

Enum members are the deliberate exception: ``StrEnum`` and ``IntEnum`` are
legitimate scalar subclasses and carry their own tagged encoding.
"""

from __future__ import annotations

from collections import defaultdict
from enum import IntEnum, StrEnum
from typing import Any, NamedTuple

import pytest

from arvis.kernel_core.canonicalization import (
    NonCanonicalizableError,
    canonical_hash,
    canonicalize,
)


class UserId(str):
    pass


class Count(int):
    pass


class Point(NamedTuple):
    x: int
    y: int


class Mode(StrEnum):
    FAST = "fast"


class Level(IntEnum):
    HIGH = 3


class TypedId(str):
    """A subclass that declares how it wants to be bound."""

    def __arvis_canonical__(self) -> dict[str, Any]:
        return {"kind": "typed_id", "value": str(self)}


def test_a_string_subclass_no_longer_aliases_its_parent():
    with pytest.raises(NonCanonicalizableError):
        canonicalize(UserId("alice"))


def test_an_int_subclass_no_longer_aliases_its_parent():
    with pytest.raises(NonCanonicalizableError):
        canonicalize(Count(3))


def test_a_container_subclass_is_refused():
    with pytest.raises(NonCanonicalizableError):
        canonicalize(defaultdict(list))

    with pytest.raises(NonCanonicalizableError):
        canonicalize(Point(1, 2))


def test_a_subclass_nested_in_a_payload_is_refused():
    """The check must hold wherever the value sits, not only at the root."""
    with pytest.raises(NonCanonicalizableError):
        canonicalize({"user": UserId("alice")})


def test_a_subclass_used_as_a_dict_key_is_refused():
    with pytest.raises(NonCanonicalizableError):
        canonicalize({UserId("alice"): "value"})


def test_a_declared_serializer_is_honoured_and_stays_distinct():
    """Opting in binds the value by its own type, never as a bare string."""
    assert canonical_hash(TypedId("alice")) != canonical_hash("alice")
    assert canonical_hash(TypedId("alice")) == canonical_hash(TypedId("alice"))
    assert canonical_hash(TypedId("alice")) != canonical_hash(TypedId("bob"))


def test_native_types_are_unaffected():
    for value in ("alice", 3, True, 1.5, b"x", {"a": 1}, [1, 2], (1, 2), {1, 2}):
        canonicalize(value)


def test_enum_members_remain_the_exception():
    """StrEnum and IntEnum are scalar subclasses with their own tagged form."""
    assert canonical_hash(Mode.FAST) != canonical_hash("fast")
    assert canonical_hash(Level.HIGH) != canonical_hash(3)
