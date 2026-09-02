# tests/api/test_canonical_ir_consistency.py
"""The public IR hash tool reproduces the hashes the engine commits.

Campaign INTEGRITY (LOT I2 / DM-I2, audit P0-5, 2026-09-02). Probed
on the pre-campaign tree: ``hash_ir({"a": "é"})`` differed from
the digest the result view computes over the same payload, because
the public helper serialized with ``ensure_ascii=False`` while the
view committed ascii bytes; and a NaN slipped through the public
helper into non-JSON canonical text without an error. An integrator
following the exported API could not verify what the engine signed.

Pinned here: one canonical JSON parameter set; the public helper
reproduces both committed digests (``view.ir_hash`` over the
detached payload, ``meta.canonical_hash`` over the hash-free IR);
non-finite floats refuse loudly.
"""

from __future__ import annotations

import copy

import pytest

from arvis.api.engine import ArvisEngine
from arvis.api.ir_canonical import canonicalize_ir, hash_ir
from arvis.ir.serialization.canonical_json import (
    canonical_json,
    canonical_json_hash,
)


def test_hash_ir_recomposes_the_global_commitment() -> None:
    """The full external-verifier recipe, end to end: strip the
    commitment_inputs sibling block (injected after hashing, D-a),
    hash the cognitive IR with the PUBLIC tool, recompose the global
    commitment, and match what the engine published.

    RED on the pre-campaign tree for any non-ASCII content: the
    public hash_ir produced different bytes than the view committed."""
    from arvis.api.commitment import compose_global_commitment

    view = ArvisEngine().run("u1", {"text": "café énergie"})
    ir = view._ir
    assert isinstance(ir, dict)
    inputs = ir.get("commitment_inputs")
    assert isinstance(inputs, dict)
    cognitive_ir = {k: v for k, v in ir.items() if k != "commitment_inputs"}

    recomposed = compose_global_commitment(
        ir_hash=hash_ir(cognitive_ir),
        timeline_commitment=view.timeline_commitment,
        commitment_inputs=inputs,
    )

    assert view.global_commitment is not None
    assert recomposed == view.global_commitment


def test_hash_ir_reproduces_meta_canonical_hash() -> None:
    view = ArvisEngine().run("u1", {"text": "café"})
    ir = view._ir
    assert isinstance(ir, dict)
    hash_free = copy.deepcopy({k: v for k, v in ir.items() if k != "commitment_inputs"})
    recorded = hash_free["meta"].pop("canonical_hash")

    assert hash_ir(hash_free) == recorded


def test_canonical_text_is_ascii() -> None:
    """RED on the pre-campaign tree: the helper emitted raw UTF-8."""
    text = canonicalize_ir({"a": "é"})
    assert text == '{"a":"\\u00e9"}'


def test_non_finite_floats_refuse_loudly() -> None:
    """RED on the pre-campaign tree: NaN serialized silently into
    non-JSON canonical text."""
    with pytest.raises(ValueError):
        hash_ir({"a": float("nan")})
    with pytest.raises(ValueError):
        canonical_json({"a": float("inf")})


def test_the_single_helper_backs_the_public_tool() -> None:
    payload = {"z": 1, "a": {"nested": [1, 2, "é"]}}
    assert hash_ir(payload) == canonical_json_hash(payload)
