# tests/conftest.py

import sys
from pathlib import Path
import pytest

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext

# force pytest to use the local repo version of arvis
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def pipeline():
    return CognitivePipeline()


@pytest.fixture
def ctx():
    return CognitivePipelineContext(
        user_id="test-user",
        cognitive_input={
            "query": "test"
        }
    )


class DummyIR:
    def to_dict(self):
        return {"ok": True}


class DummyPipelineResult:
    ir_input = DummyIR()
    ir_context = DummyIR()
    ir_decision = DummyIR()
    ir_state = DummyIR()
    ir_gate = DummyIR()


@pytest.fixture
def dummy_pipeline_result():
    return DummyPipelineResult()