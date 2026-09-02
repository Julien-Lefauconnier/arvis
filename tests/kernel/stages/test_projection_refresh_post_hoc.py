# tests/kernel/stages/test_projection_refresh_post_hoc.py
"""Campaign PROJ, RED-first: the published certificate is the one
that decided.

``PipelineObservabilityService`` refreshes the projection during
finalize, after the verdict is decided, and the refresh used to run
the full projection again and OVERWRITE ``ctx.projection.certificate``
plus every decision field around it (view, margins, the exported
certification level). Measured on the smoke corpus: 42 of 42 turns
published a certificate different from the one the gate consumed,
materially different on 18 (the gate decided on LOCAL with the
Lyapunov axis unassessed, the trace published BASIC with
``lyapunov_compatibility_ok=False``). The audit trail contradicted
the decision, on the system whose reason to exist is proving what
happened.

DM-P2: the refresh becomes a POST-HOC ATTESTATION. It re-validates
the decision's own view against the signals that only exist after
the gate (the composite energy delta), and publishes under distinct
names (``post_certificate``, ``projection_post_certification_level``).
The decision certificate, view and exported level are never rewritten,
so everything downstream that reads the certificate (the IR adapter
included) now reads what actually decided.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.projection_stage import ProjectionStage


class _State:
    def to_projection_view(self):
        return {"state.system_tension": 0.4}


class _PiImpl:
    def project(self, ctx):
        return _State()

    def project_previous(self, ctx):
        return None


class _CountingValidator:
    """Distinguishable certificates per call, so any overwrite of the
    first (decision) certificate by the second (refresh) is visible."""

    def __init__(self) -> None:
        self.calls = 0

    def validate(self, projection_view, previous_projected=None, ctx=None):
        self.calls += 1
        call_index = self.calls
        return SimpleNamespace(
            domain_valid=True,
            margin_to_boundary=1.0,
            is_projection_safe=True,
            lyapunov_compatibility_ok=call_index == 1,
            certification_level=SimpleNamespace(
                value="LOCAL" if call_index == 1 else "BASIC"
            ),
            checks_detail={"call_index": call_index},
        )


def _pipeline() -> SimpleNamespace:
    return SimpleNamespace(pi_impl=_PiImpl(), projection_validator=_CountingValidator())


def _ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(user_id="test", cognitive_input={})


def test_refresh_never_rewrites_the_decision_certificate() -> None:
    stage = ProjectionStage()
    pipeline = _pipeline()
    ctx = _ctx()

    stage.run(pipeline, ctx)
    decision = ctx.projection.certificate
    decision_level = ctx.extra["projection_certification_level"]

    stage.refresh(pipeline, ctx)

    assert ctx.projection.certificate is decision
    assert ctx.extra["projection_certification_level"] == decision_level


def test_refresh_publishes_a_distinct_post_hoc_attestation() -> None:
    stage = ProjectionStage()
    pipeline = _pipeline()
    ctx = _ctx()

    stage.run(pipeline, ctx)
    stage.refresh(pipeline, ctx)

    post = ctx.projection.post_certificate
    assert post is not None
    assert post is not ctx.projection.certificate
    assert ctx.extra["projection_post_certification_level"] == "BASIC"
    assert ctx.extra["projection_post_lyapunov_compatible"] is False


def test_refresh_revalidates_the_decision_view_not_a_new_one() -> None:
    """The attestation answers "what do we now know about the
    projection that decided", so it validates that same view."""
    seen: list[dict] = []

    class _SpyValidator(_CountingValidator):
        def validate(self, projection_view, previous_projected=None, ctx=None):
            seen.append(dict(projection_view))
            return super().validate(
                projection_view, previous_projected=previous_projected, ctx=ctx
            )

    stage = ProjectionStage()
    pipeline = SimpleNamespace(pi_impl=_PiImpl(), projection_validator=_SpyValidator())
    ctx = _ctx()

    stage.run(pipeline, ctx)
    decision_view = dict(ctx.projection.view)
    stage.refresh(pipeline, ctx)

    assert len(seen) == 2
    assert seen[1] == decision_view
    assert dict(ctx.projection.view) == decision_view


def test_refresh_without_a_decision_projection_publishes_nothing() -> None:
    """A turn whose projection never ran has nothing to attest."""
    stage = ProjectionStage()
    pipeline = _pipeline()
    ctx = _ctx()

    stage.refresh(pipeline, ctx)

    assert ctx.projection.post_certificate is None
    assert "projection_post_certification_level" not in ctx.extra
