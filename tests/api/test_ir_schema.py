# tests/api/test_ir_schema.py

import json
from jsonschema import validate

from arvis.api.ir import build_ir_view


def test_ir_matches_schema(dummy_pipeline_result):
    with open("arvis/api/schema/ir_schema.json") as f:
        schema = json.load(f)

    ir = build_ir_view(dummy_pipeline_result)

    validate(instance=ir, schema=schema)