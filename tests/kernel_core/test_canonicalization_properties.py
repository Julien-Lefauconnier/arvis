# tests/kernel_core/test_canonicalization_properties.py
"""Property-based injectivity of canonicalization (campaign 6, Lot 0).

The directed suite pins every collision the audits reproduced; this
module states the general contract over the officially injective
domain: for any two values drawn from the supported domain,

    canonical_bytes(x) == canonical_bytes(y)  implies  x == y

which is the contrapositive of injectivity up to Python equality. The
domain strategy mirrors the docstring of
:mod:`arvis.kernel_core.canonicalization`: JSON scalars with finite
floats, bytes/bytearray, datetimes, dates, Decimals, UUIDs, paths,
and recursive lists/tuples/dicts built over them. Sets are exercised
separately (their membership semantics make cross-type equality
subtle) and hashable-only leaves are used inside them.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import PurePosixPath
from uuid import UUID

from hypothesis import given, settings
from hypothesis import strategies as st

from arvis.kernel_core.canonicalization import canonical_bytes

_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**63), max_value=2**63),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=20),
    st.binary(max_size=20),
    st.binary(max_size=20).map(bytearray),
    st.datetimes(timezones=st.just(UTC) | st.none()),
    st.dates(),
    st.decimals(allow_nan=False, allow_infinity=False),
    st.uuids(),
    st.text(alphabet="abc/", min_size=1, max_size=10).map(PurePosixPath),
)

_values = st.recursive(
    _scalars,
    lambda children: st.one_of(
        st.lists(children, max_size=4),
        st.lists(children, max_size=4).map(tuple),
        st.dictionaries(
            st.one_of(st.text(max_size=8), st.integers(), st.booleans()),
            children,
            max_size=4,
        ),
    ),
    max_leaves=12,
)

_hashable_scalars = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**31), max_value=2**31),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(max_size=10),
    st.binary(max_size=10),
)


@settings(max_examples=300)
@given(_values, _values)
def test_equal_canonical_bytes_implies_equal_values(x: object, y: object) -> None:
    if canonical_bytes(x) == canonical_bytes(y):
        assert x == y


@settings(max_examples=200)
@given(_values)
def test_canonical_bytes_is_deterministic(x: object) -> None:
    assert canonical_bytes(x) == canonical_bytes(x)


@settings(max_examples=200)
@given(st.sets(_hashable_scalars, max_size=5), st.sets(_hashable_scalars, max_size=5))
def test_set_injectivity(x: set[object], y: set[object]) -> None:
    if canonical_bytes(x) == canonical_bytes(y):
        assert x == y


@settings(max_examples=100)
@given(st.frozensets(_hashable_scalars, max_size=5))
def test_set_vs_frozenset_never_alias(x: frozenset[object]) -> None:
    assert canonical_bytes(set(x)) != canonical_bytes(x)


_example_uuid = UUID("00000000-0000-0000-0000-000000000000")
_example_probe: list[object] = [
    _example_uuid,
    str(_example_uuid),
    Decimal("1"),
    1,
    1.0,
    True,
    b"1",
    bytearray(b"1"),
    "1",
    date(2026, 1, 1),
    datetime(2026, 1, 1),
    PurePosixPath("1"),
]


def test_cross_type_probe_all_distinct() -> None:
    """Every pair of same-content different-type values stays distinct."""
    seen: dict[bytes, object] = {}
    for value in _example_probe:
        blob = canonical_bytes(value)
        assert blob not in seen, (value, seen[blob])
        seen[blob] = value
