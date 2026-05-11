# tests/fixtures/contexts.py

import pytest

from tests.fixtures.builders.context_builder import (
    build_test_context,
)


@pytest.fixture
def minimal_ctx():
    return build_test_context()


@pytest.fixture
def unstable_ctx():
    return build_test_context(
        drift_score=0.9,
        collapse_risk=0.8,
        regime="critical",
    )
