# tests/fixtures/test_builders_seed_canonical_channels.py
"""The shared test builders seed the channels the pipeline reads.

Campaign OBS (decision DS5). ``build_test_context`` historically seeded
``ctx.observability.system_tension``, a dynamic attribute on the
observability container that NOTHING reads: the canonical channel is
``ctx.observability.diagnostics.system_tension`` (consumed by the
projection, the decision trace and the state IR adapter). The tension
seeded by tests therefore never reached the projection. These pins
keep every builder seed on a canonical, actually-consumed path.
"""

from __future__ import annotations

from tests.fixtures.builders.context_builder import build_test_context


def test_system_tension_seed_reaches_the_canonical_channel() -> None:
    ctx = build_test_context(system_tension=0.7)

    assert ctx.observability.diagnostics.system_tension == 0.7


def test_no_seed_lands_outside_the_bounded_contexts() -> None:
    """The builder must not create dynamic attributes on the containers:
    a seed outside the declared fields is invisible to every reader."""
    ctx = build_test_context()

    assert "system_tension" not in vars(ctx.observability)
