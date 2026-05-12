# tests/conftest.py

import sys
from pathlib import Path

import pytest

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from tests.fixtures.builders.context_builder import (
    build_test_context,
    build_test_context_with_ir,
)

# force pytest to use the local repo version of arvis
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# ============================================================
# Global pytest fixture modules
# ============================================================
pytest_plugins = [
    "tests.fixtures.errors",
    "tests.fixtures.projections",
]


@pytest.fixture
def pipeline():
    return CognitivePipeline()


@pytest.fixture
def ctx():
    return CognitivePipelineContext(
        user_id="test-user", cognitive_input={"query": "test"}
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


# ============================================================
# 🧪 Shared fixtures for Π / projection / gate tests
# ============================================================


@pytest.fixture
def minimal_ctx():
    """
    Minimal but realistic context for Π structured tests.
    Must stay ZKCS-safe and numeric.
    """
    return build_test_context()


@pytest.fixture
def ctx_with_ir():
    return build_test_context_with_ir()
