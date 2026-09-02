# tests/kernel_core/test_canonicalization_dataclass_state.py
"""Campaign KERNEL (LOT K1), RED-first: a dataclass must not hide
instance state from the injective encoder.

The dataclass branch built its material from ``fields(obj)`` alone, so
anything set on the instance beyond the declared fields was invisible
and the private-attribute refusal of ``_object_attributes`` was never
reached. Two materially different payments therefore shared a
canonical hash, which is exactly the aliasing the module's docstring
says it refuses (campaign 6, finding 7.4) and which a commitment or a
confirmation is minted from: an engagement approved for one effect
was redeemable for another.

A plain object carrying the same private attribute WAS correctly
refused, so the two paths disagreed on the same question.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from arvis.kernel_core.canonicalization import (
    NonCanonicalizableError,
    canonical_hash,
)


@dataclass
class Payment:
    amount: int


def test_an_undeclared_attribute_changes_the_hash() -> None:
    plain = Payment(amount=100)
    diverted = Payment(amount=100)
    diverted.beneficiary = "attacker-iban"  # type: ignore[attr-defined]

    assert canonical_hash(plain) != canonical_hash(diverted)


def test_a_private_attribute_is_refused_on_a_dataclass_too() -> None:
    """The plain-object path already refuses this; the dataclass path
    must answer the same question the same way."""
    obj = Payment(amount=100)
    obj._endpoint = "https://evil"  # type: ignore[attr-defined]

    with pytest.raises(NonCanonicalizableError):
        canonical_hash(obj)


def test_a_clean_dataclass_still_canonicalizes() -> None:
    """The fix must not refuse ordinary dataclasses: same declared
    state, same hash; different declared state, different hash."""
    assert canonical_hash(Payment(amount=100)) == canonical_hash(Payment(amount=100))
    assert canonical_hash(Payment(amount=100)) != canonical_hash(Payment(amount=101))


def test_an_unset_field_is_refused_not_encoded_as_none() -> None:
    """``getattr(obj, name, None)`` silently encoded a never-assigned
    field as None, aliasing it with an explicit None."""

    @dataclass
    class Deferred:
        computed: int = field(init=False)

    obj = Deferred()

    with pytest.raises(NonCanonicalizableError):
        canonical_hash(obj)


def test_nested_dataclass_state_is_covered_too() -> None:
    @dataclass
    class Envelope:
        payment: Payment

    clean = Envelope(payment=Payment(amount=100))
    hidden_inner = Payment(amount=100)
    hidden_inner.beneficiary = "attacker-iban"  # type: ignore[attr-defined]
    tampered = Envelope(payment=hidden_inner)

    assert canonical_hash(clean) != canonical_hash(tampered)
