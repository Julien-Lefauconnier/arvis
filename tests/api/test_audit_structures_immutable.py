# tests/api/test_audit_structures_immutable.py

"""Audit artifact immutability contract (F-013).

The audit artifact is the pair (IR payload, global_commitment). The
reproducibility guarantee is sealed at the commitment boundary: the
stored IR is detached from live pipeline structures at hash time, and
exports are defensive copies, so no mutation, however deep, can
diverge the payload from its commitment.
"""

import copy
import json
from hashlib import sha256

from arvis.api.os import CognitiveOS


def _mutate_recursively(obj):
    if isinstance(obj, dict):
        for value in list(obj.values()):
            _mutate_recursively(value)
        obj["__mutated__"] = True
    elif isinstance(obj, list):
        for value in obj:
            _mutate_recursively(value)
        obj.append("__mutated__")


def test_recursive_mutation_of_export_cannot_diverge_commitment():
    os = CognitiveOS()
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.global_commitment is not None

    baseline = copy.deepcopy(view.to_ir())
    exported = view.to_ir()
    _mutate_recursively(exported)

    # The view is untouched by mutation of its export.
    assert view.to_ir() == baseline

    # A fresh export still replays and verifies against the original
    # commitment.
    replayed = os.replay_verified(
        view.to_ir(),
        expected_global_commitment=view.global_commitment,
    )
    assert replayed.global_commitment == view.global_commitment


def test_view_ir_is_exactly_the_hashed_canonical_payload():
    from arvis.api.commitment import compose_global_commitment

    os = CognitiveOS()
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    assert view.timeline_commitment is not None

    exported = view.to_ir()
    declared = exported.pop("commitment_inputs")

    ir_bytes = json.dumps(
        exported,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    ir_hash = sha256(ir_bytes).hexdigest()

    expected = compose_global_commitment(
        ir_hash=ir_hash,
        timeline_commitment=view.timeline_commitment,
        commitment_inputs=declared,
    )
    assert view.global_commitment == expected


def test_replay_does_not_mutate_the_input_ir():
    os = CognitiveOS()
    view = os.run(user_id="u1", cognitive_input={"text": "hello"})
    ir = view.to_ir()
    snapshot = copy.deepcopy(ir)
    os.replay_verified(ir, expected_global_commitment=view.global_commitment)
    assert ir == snapshot
