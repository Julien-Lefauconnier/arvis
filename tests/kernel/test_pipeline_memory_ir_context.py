# tests/kernel/test_pipeline_memory_ir_context.py

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext


def test_bootstrap_ir_context_prefers_memory_projection():
    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input={},
        long_memory={"preferences": {"language": False}, "constraints": ["legacy"]},
    )
    ctx.memory_projection = {
        "preferences": {"language": True, "timezone": True},
        "constraints": ["no_tracking"],
        "memory_pressure": 2,
        "has_constraints": True,
        "has_timezone": True,
        "has_language_pref": True,
    }

    pipeline._bootstrap_ir_context(ctx)

    assert ctx.ir_context is not None
    assert ctx.ir_context.long_memory_preferences == {
        "language": True,
        "timezone": True,
    }
    assert ctx.ir_context.long_memory_constraints == ("no_tracking",)
    assert ctx.ir_context.extra["memory_pressure"] == 2
    assert ctx.ir_context.extra["has_constraints"] is True
    assert ctx.ir_context.extra["has_timezone"] is True
    assert ctx.ir_context.extra["has_language_pref"] is True


def test_bootstrap_ir_context_falls_back_to_long_memory():
    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input={},
        long_memory={
            "preferences": {"language": True},
            "constraints": ["no_share"],
        },
    )

    pipeline._bootstrap_ir_context(ctx)

    assert ctx.ir_context is not None
    assert ctx.ir_context.long_memory_preferences == {"language": True}
    assert ctx.ir_context.long_memory_constraints == ("no_share",)


def test_bootstrap_ir_context_keeps_existing_ir_context():
    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input={},
    )
    pipeline._bootstrap_ir_context(ctx)
    first = ctx.ir_context

    ctx.memory_projection = {
        "preferences": {"language": True},
        "constraints": ["no_tracking"],
    }

    pipeline._bootstrap_ir_context(ctx)

    assert ctx.ir_context is first



def test_bootstrap_ir_context_exposes_memory_projection_safely():
    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input={},
        long_memory={
            "constraints": ["no_tracking"],
            "preferences": {"language": True},
        },
    )
    ctx.memory_projection = {
        "memory_pressure": 0.8,
        "has_constraints": True,
        "constraints": ["no_tracking", "no_override"],
        "has_language_pref": True,
        "has_timezone": True,
    }

    pipeline._bootstrap_ir_context(ctx)

    ir = ctx.ir_context
    assert ir is not None

    assert ir.memory_present is True
    assert ir.memory_pressure == 0.8
    assert ir.memory_has_constraints is True
    assert ir.memory_constraint_count == 2
    assert ir.memory_has_language_pref is True
    assert ir.memory_has_timezone is True


def test_bootstrap_ir_context_memory_projection_defaults_are_safe():
    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input={},
        long_memory={},
    )
    ctx.memory_projection = None

    pipeline._bootstrap_ir_context(ctx)

    ir = ctx.ir_context
    assert ir is not None

    assert ir.memory_present is False
    assert ir.memory_pressure == 0.0
    assert ir.memory_has_constraints is False
    assert ir.memory_constraint_count == 0
    assert ir.memory_has_language_pref is False
    assert ir.memory_has_timezone is False


def test_bootstrap_ir_context_does_not_expose_raw_memory_entries():
    pipeline = CognitivePipeline()

    ctx = CognitivePipelineContext(
        user_id="u1",
        cognitive_input={},
        long_memory={},
    )
    ctx.memory_projection = {
        "memory_pressure": 0.5,
        "has_constraints": False,
        "entries": ["should_not_leak"],
        "raw_values": {"secret": "forbidden"},
    }

    pipeline._bootstrap_ir_context(ctx)

    ir = ctx.ir_context
    assert ir is not None

    assert ir.memory_present is True
    assert ir.memory_pressure == 0.5

    # nothing raw should be exported into canonical fields
    assert "entries" not in ir.extra
    assert "raw_values" not in ir.extra