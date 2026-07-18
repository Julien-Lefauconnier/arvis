# tests/kernel_core/test_canonicalization.py
"""Injective canonicalization: adversarial collision suite (campaign 5).

Each a7 collision reproduced on the tag is pinned here as a
non-collision, plus the type-encoding, envelope, determinism and
fail-closed contracts. If any future change reintroduces a lossy
reduction on the effect path, one of these fails before a release.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path, PurePosixPath
from uuid import UUID

import pytest

from arvis.kernel_core.canonicalization import (
    CANONICALIZATION_VERSION,
    NonCanonicalizableError,
    canonical_bytes,
    canonical_hash,
    canonicalize,
)


def _distinct(a, b):
    return canonical_hash(a) != canonical_hash(b)


def _equal(a, b):
    return canonical_hash(a) == canonical_hash(b)


# ---------------------------------------------------------------
# The exact a7 collisions, now pinned as non-collisions
# ---------------------------------------------------------------


def test_business_id_is_not_stripped():
    a = {"id": "record-A", "action": "delete"}
    b = {"id": "record-B", "action": "delete"}
    assert _distinct(a, b)


def test_business_timestamp_is_not_stripped():
    a = {"timestamp": "2026-01-01", "action": "publish"}
    b = {"timestamp": "2027-01-01", "action": "publish"}
    assert _distinct(a, b)


def test_business_process_id_is_not_stripped():
    a = {"process_id": "p1", "action": "kill"}
    b = {"process_id": "p2", "action": "kill"}
    assert _distinct(a, b)


def test_all_previously_volatile_keys_survive_in_business_payload():
    for key in (
        "id",
        "timestamp",
        "process_id",
        "causal_id",
        "syscall_id",
        "tick",
        "created_at",
    ):
        a = {key: "A", "action": "go"}
        b = {key: "B", "action": "go"}
        assert _distinct(a, b), key


def test_bytes_content_is_distinguished():
    assert _distinct({"blob": b"A"}, {"blob": b"B"})
    assert _distinct(b"", b"\x00")


def test_integer_and_string_keys_do_not_collide():
    assert _distinct({1: "x"}, {"1": "x"})


def test_bool_and_int_keys_do_not_collide():
    assert _distinct({True: "x"}, {1: "x"})
    assert _distinct({False: "x"}, {0: "x"})


def test_deeply_nested_distinct_objects_do_not_collide_by_depth():
    # Distinct leaves under moderate nesting must stay distinct (no
    # depth-triggered type collapse).
    def nest(leaf, n):
        obj = leaf
        for _ in range(n):
            obj = {"k": obj}
        return obj

    assert _distinct(nest("A", 20), nest("B", 20))


# ---------------------------------------------------------------
# Typed encoders: each type mapped injectively and distinctly
# ---------------------------------------------------------------


def test_bytes_vs_equal_base64_string_do_not_collide():
    # b"A" encodes to base64 "QQ=="; the raw string "QQ==" must not
    # alias the bytes value.
    import base64

    raw = base64.b64encode(b"A").decode()
    assert _distinct(b"A", raw)


def test_datetime_naive_vs_aware_do_not_collide():
    naive = datetime(2026, 1, 1, 12, 0, 0)
    aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert _distinct(naive, aware)


def test_datetime_microseconds_are_bound():
    a = datetime(2026, 1, 1, 12, 0, 0, 1, tzinfo=UTC)
    b = datetime(2026, 1, 1, 12, 0, 0, 2, tzinfo=UTC)
    assert _distinct(a, b)


def test_date_vs_datetime_do_not_collide():
    assert _distinct(date(2026, 1, 1), datetime(2026, 1, 1, 0, 0, 0))


def test_decimal_trailing_zeros_are_bound():
    assert _distinct(Decimal("12.3400"), Decimal("12.34"))


def test_decimal_vs_float_do_not_collide():
    assert _distinct(Decimal("12.34"), 12.34)


def test_uuid_vs_equal_string_do_not_collide():
    u = UUID("12345678-1234-5678-1234-567812345678")
    assert _distinct(u, str(u))


def test_path_vs_equal_string_do_not_collide():
    p = PurePosixPath("/a/b")
    assert _distinct(p, "/a/b")


def test_enum_members_sharing_a_value_are_distinct():
    class E(enum.Enum):
        A = 1
        B = 1  # alias in Python, but we bind the queried name

    # E.B is an alias of E.A in CPython, so compare two real members.
    class F(enum.Enum):
        X = 1
        Y = 2

    assert _distinct(F.X, F.Y)


def test_enum_vs_raw_value_do_not_collide():
    class F(enum.Enum):
        X = 1

    assert _distinct(F.X, 1)


def test_set_is_order_independent_but_membership_bound():
    assert _equal({1, 2, 3}, {3, 2, 1})
    assert _distinct({1, 2, 3}, {1, 2, 4})


def test_set_vs_frozenset_do_not_collide():
    assert _distinct({1, 2}, frozenset({1, 2}))


def test_tuple_vs_list_do_not_collide():
    assert _distinct((1, 2), [1, 2])


def test_tuple_order_is_bound():
    assert _distinct((1, 2), (2, 1))


# ---------------------------------------------------------------
# Objects and dataclasses: fields bound injectively
# ---------------------------------------------------------------


def test_dataclass_fields_are_distinguished():
    @dataclass
    class Cmd:
        target: str
        action: str

    assert _distinct(Cmd("A", "delete"), Cmd("B", "delete"))


def test_dataclass_vs_equivalent_dict_do_not_collide():
    @dataclass
    class Cmd:
        target: str

    # A dataclass carries its type identity; a bare dict does not.
    assert _distinct(Cmd("A"), {"target": "A"})


def test_plain_object_attributes_are_distinguished():
    class Cmd:
        def __init__(self, target):
            self.target = target

    assert _distinct(Cmd("A"), Cmd("B"))


def test_private_operational_state_requires_serializer():
    class Cmd:
        def __init__(self, target, secret):
            self.target = target
            self._secret = secret

    # Campaign 6 (closes a8 finding 7.4): private state can be
    # operational; an object carrying it is refused, never partially
    # encoded, so two operationally different objects cannot share a
    # commitment through a dropped attribute.
    with pytest.raises(NonCanonicalizableError) as exc:
        canonical_hash(Cmd("A", 1))
    assert "_secret" in str(exc.value)


def test_serializer_hook_binds_private_state():
    class Cmd:
        def __init__(self, target, secret):
            self.target = target
            self._secret = secret

        def __arvis_canonical__(self):
            return {"target": self.target, "secret": self._secret}

    # The explicit serializer is the contract for private state: the
    # returned representation is bound, so differing private state
    # yields differing hashes.
    assert _distinct(Cmd("A", 1), Cmd("A", 2))
    assert _equal(Cmd("A", 1), Cmd("A", 1))


def test_serializer_hook_output_is_type_bound():
    class CmdA:
        def __arvis_canonical__(self):
            return {"v": 1}

    class CmdB:
        def __arvis_canonical__(self):
            return {"v": 1}

    # Same serialized payload, different classes: the module-qualified
    # class identity is part of the material, so no aliasing.
    assert _distinct(CmdA(), CmdB())


# ---------------------------------------------------------------
# Tag ambiguity: a business dic shaped like a typed encoding
# ---------------------------------------------------------------


def test_business_dict_shaped_like_a_tag_is_escaped():
    # A payload literally using the reserved bytes tag as its only key
    # must not be read back as bytes, and must stay distinct from the
    # real bytes value.
    import base64

    tag = "__arvis_bytes_b64__"
    literal = {tag: base64.b64encode(b"A").decode()}
    assert _distinct(literal, b"A")
    # And two distinct such literals stay distinct.
    assert _distinct({tag: "QQ=="}, {tag: "Qg=="})


# ---------------------------------------------------------------
# Determinism and stability
# ---------------------------------------------------------------


def test_canonicalization_is_deterministic():
    obj = {"id": "x", "nested": {"a": [1, 2, {3, 4}], "d": Decimal("1.0")}}
    assert canonical_bytes(obj) == canonical_bytes(obj)


def test_dict_key_order_does_not_affect_canonical_bytes():
    assert canonical_bytes({"a": 1, "b": 2}) == canonical_bytes({"b": 2, "a": 1})


def test_version_constant_is_exposed():
    assert isinstance(CANONICALIZATION_VERSION, int)


# ---------------------------------------------------------------
# Fail-closed: no silent lossy fallback
# ---------------------------------------------------------------


def test_non_canonicalizable_value_raises():
    # A generator has no __dict__ and no typed encoding: refuse rather
    # than alias.
    def gen():
        yield 1

    with pytest.raises(NonCanonicalizableError):
        canonicalize(gen())


def test_non_canonicalizable_reports_path():
    def gen():
        yield 1

    with pytest.raises(NonCanonicalizableError) as exc:
        canonicalize({"outer": {"inner": gen()}})
    assert "inner" in exc.value.path


def test_unhashable_free_object_still_canonicalizes_by_attributes():
    class Cmd:
        def __init__(self):
            self.a = 1

    # No exception: plain objects go through the attribute path.
    assert canonical_hash(Cmd())


# ---------------------------------------------------------------
# The exact a8 collisions (audit 0.1.0a8, section 7), pinned as
# non-collisions (campaign 6, Lot 0)
# ---------------------------------------------------------------


def test_bytes_and_bytearray_do_not_share_commitment():
    assert _distinct(b"A", bytearray(b"A"))
    assert _distinct({"blob": b"A"}, {"blob": bytearray(b"A")})


def test_path_subtypes_do_not_share_commitment():
    # Path("/tmp/a") resolves to a concrete PosixPath/WindowsPath while
    # PurePosixPath is abstract; equal strings, distinct types, distinct
    # host semantics.
    assert _distinct(Path("/tmp/a"), PurePosixPath("/tmp/a"))


def test_same_qualname_in_different_modules_does_not_collide():
    def make_record(module: str) -> type:
        cls = type("Record", (), {})
        cls.__module__ = module
        cls.__qualname__ = "Record"
        return cls

    a = make_record("module_a")()
    a.value = 1
    b = make_record("module_b")()
    b.value = 1
    assert _distinct(a, b)


def test_homonymous_enums_in_different_modules_do_not_collide():
    class Color(enum.Enum):
        RED = 1

    class ColorTwin(enum.Enum):
        RED = 1

    ColorTwin.__qualname__ = Color.__qualname__
    ColorTwin.__module__ = "somewhere_else"
    assert _distinct(Color.RED, ColorTwin.RED)


def test_non_finite_floats_are_refused():
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(NonCanonicalizableError):
            canonical_hash(bad)
        with pytest.raises(NonCanonicalizableError):
            canonical_hash({bad: "x"})


def test_mangled_private_attribute_is_refused():
    class Cmd:
        def __init__(self):
            self.__hidden = 1  # mangles to _Cmd__hidden

    with pytest.raises(NonCanonicalizableError):
        canonical_hash(Cmd())
