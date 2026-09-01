# tests/kernel/test_context_accessor_fallbacks.py
"""Accessor duck fallbacks: canonical first, root attribute second.

Campaign RELEASE (LOT R2). The observability accessors serve
duck-tolerant callsites (projection, adapters): on a real context
they read the canonical sub-context; on a mock without the
observability container they fall back to the historical root
attribute; and the tooling installer refuses a mistyped container
instead of silently working around it.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.context.observability_accessors import (
    cognitive_state,
    global_forecast,
    global_stability,
    ir_state,
    multi_horizon,
    predictive_snapshot,
    symbolic_drift,
    symbolic_features,
)
from arvis.kernel.pipeline.context.tooling_accessors import tooling

_ACCESSORS = [
    ("predictive_snapshot", predictive_snapshot),
    ("global_stability", global_stability),
    ("global_forecast", global_forecast),
    ("multi_horizon", multi_horizon),
    ("symbolic_drift", symbolic_drift),
    ("symbolic_features", symbolic_features),
    ("ir_state", ir_state),
    ("cognitive_state", cognitive_state),
]


def test_canonical_container_wins_on_a_real_context() -> None:
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    sentinel = object()
    ctx.observability.projections.predictive_snapshot = sentinel
    ctx.observability.state.ir_state = sentinel
    ctx.observability.symbolic.symbolic_drift = sentinel

    assert predictive_snapshot(ctx) is sentinel
    assert ir_state(ctx) is sentinel
    assert symbolic_drift(ctx) is sentinel


def test_duck_without_observability_falls_back_to_root_attribute() -> None:
    for name, accessor in _ACCESSORS:
        sentinel = object()
        duck = SimpleNamespace(**{name: sentinel})

        assert accessor(duck) is sentinel, name


def test_bare_duck_reads_none_everywhere() -> None:
    duck = SimpleNamespace()

    for name, accessor in _ACCESSORS:
        assert accessor(duck) is None, name


def test_tooling_installer_installs_on_ducks_and_refuses_mistypes() -> None:
    duck = SimpleNamespace()

    installed = tooling(duck)
    installed.tool_failure = True

    # same container on the second access
    assert tooling(duck) is installed

    with pytest.raises(TypeError, match="PipelineToolingContext"):
        tooling(SimpleNamespace(tooling="not a container"))
