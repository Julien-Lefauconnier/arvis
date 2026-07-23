# tests/ir/test_witness_single_serialization.py

"""The IR witness, its hash and its envelope share one serialization.

Audit a13, P1-04: the pipeline used to serialize the live IR three
times (witness dict, hash, envelope), so a mutation of the IR between
those steps could desynchronize the exported witness from its hash at
birth. The pipeline now serializes once and derives every artifact from
the same canonical text; these tests pin that property end to end.
"""

import hashlib
import json

from arvis.ir.serialization.cognitive_ir_hasher import CognitiveIRHasher
from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)


def test_hash_of_canonical_text_matches_hash_of_the_object():
    sample = {"b": [1, 2.5, "x"], "a": {"nested": True, "n": None}}
    canonical_text = CognitiveIRSerializer.serialize(sample)
    assert CognitiveIRHasher.hash_canonical_text(
        canonical_text
    ) == CognitiveIRHasher.hash(sample)


def test_pipeline_witness_hash_and_envelope_derive_from_the_same_bytes():
    pipeline = CognitivePipeline()
    result = pipeline.run(
        CognitivePipelineContext(
            user_id="user-1",
            cognitive_input={"input_id": "witness"},
        )
    )

    ir = result.ir
    assert ir.ir_serialized is not None
    assert ir.ir_hash is not None
    assert ir.ir_envelope is not None

    recanonicalized = json.dumps(
        ir.ir_serialized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    assert hashlib.sha256(recanonicalized.encode("utf-8")).hexdigest() == ir.ir_hash, (
        "the exported witness must hash to the pinned witness hash"
    )

    assert ir.ir_envelope.hash == ir.ir_hash
    assert ir.ir_envelope.serialized == ir.ir_serialized
