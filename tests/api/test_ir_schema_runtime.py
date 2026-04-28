# tests/api/test_ir_schema_runtime.py

import json
from jsonschema import validate

from arvis.api import CognitiveOS


def load_schema():
    with open("arvis/api/schema/ir_schema.json") as f:
        return json.load(f)


def test_run_ir_matches_schema():
    os = CognitiveOS()

    ir = os.run_ir(user_id="u1", cognitive_input={})

    schema = load_schema()

    # validation stricte
    validate(instance=ir, schema=schema)


def test_run_ir_schema_multiple_runs():
    os = CognitiveOS()
    schema = load_schema()

    for _ in range(5):
        ir = os.run_ir(user_id="u1", cognitive_input={})

        validate(instance=ir, schema=schema)


def test_run_ir_contains_hash():
    from arvis.api import CognitiveOS

    os = CognitiveOS()
    ir = os.run_ir(user_id="u1", cognitive_input={})

    assert "meta" in ir
    assert "canonical_hash" in ir["meta"]
