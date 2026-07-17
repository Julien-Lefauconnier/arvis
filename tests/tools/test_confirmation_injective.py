# tests/tools/test_confirmation_injective.py
"""Injective confirmation binding: the a7 P0, closed (campaign 5, Lot 1).

The a7 audit's most severe finding: a confirmation granted to act on
record-A could be consumed to act on record-B, because the payload
commitment stripped the business ``id`` before hashing. These tests pin
the fix at the confirmation boundary end to end - not just at the
canonical encoder (covered in test_canonicalization.py), but through
``payload_commitment`` and ``ConfirmationRegistry.consume``.
"""

from __future__ import annotations

from arvis.tools.confirmation import ConfirmationRegistry, payload_commitment

# ---------------------------------------------------------------
# payload_commitment: the a7 collisions, closed
# ---------------------------------------------------------------


def test_business_id_yields_distinct_payload_commitments():
    a = payload_commitment({"id": "record-A", "action": "delete"})
    b = payload_commitment({"id": "record-B", "action": "delete"})
    assert a != b


def test_business_timestamp_yields_distinct_payload_commitments():
    a = payload_commitment({"timestamp": "2026-01-01", "action": "publish"})
    b = payload_commitment({"timestamp": "2027-01-01", "action": "publish"})
    assert a != b


def test_business_process_id_yields_distinct_payload_commitments():
    a = payload_commitment({"process_id": "p1", "action": "kill"})
    b = payload_commitment({"process_id": "p2", "action": "kill"})
    assert a != b


def test_bytes_payload_yields_distinct_payload_commitments():
    assert payload_commitment({"blob": b"A"}) != payload_commitment({"blob": b"B"})


def test_key_type_yields_distinct_payload_commitments():
    assert payload_commitment({1: "x"}) != payload_commitment({"1": "x"})


def test_identical_payload_yields_identical_commitment():
    a = payload_commitment({"id": "record-A", "action": "delete"})
    b = payload_commitment({"id": "record-A", "action": "delete"})
    assert a == b


# ---------------------------------------------------------------
# Confirmation cross-consumption: refused (the P0 absolu)
# ---------------------------------------------------------------


def test_confirmation_for_a_is_refused_for_b():
    reg = ConfirmationRegistry()
    conf = reg.issue(
        tool_name="delete_record",
        payload={"id": "record-A", "action": "delete"},
        principal="u1",
    )
    consumed = reg.consume(
        confirmation_id=conf.confirmation_id,
        tool_name="delete_record",
        payload={"id": "record-B", "action": "delete"},
        principal="u1",
    )
    assert consumed is None


def test_confirmation_for_a_still_works_for_a():
    reg = ConfirmationRegistry()
    conf = reg.issue(
        tool_name="delete_record",
        payload={"id": "record-A", "action": "delete"},
        principal="u1",
    )
    consumed = reg.consume(
        confirmation_id=conf.confirmation_id,
        tool_name="delete_record",
        payload={"id": "record-A", "action": "delete"},
        principal="u1",
    )
    assert consumed is not None


def test_refused_cross_consumption_does_not_burn_the_record():
    # A wrong-payload attempt must not consume the legitimate
    # confirmation: the record survives for its real effect.
    reg = ConfirmationRegistry()
    conf = reg.issue(
        tool_name="delete_record",
        payload={"id": "record-A", "action": "delete"},
        principal="u1",
    )
    assert (
        reg.consume(
            confirmation_id=conf.confirmation_id,
            tool_name="delete_record",
            payload={"id": "record-B", "action": "delete"},
            principal="u1",
        )
        is None
    )
    # The legitimate effect still succeeds afterwards.
    assert (
        reg.consume(
            confirmation_id=conf.confirmation_id,
            tool_name="delete_record",
            payload={"id": "record-A", "action": "delete"},
            principal="u1",
        )
        is not None
    )
