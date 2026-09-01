# arvis/kernel/pipeline/stages/gate/context.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from arvis.kernel.pipeline.context.journal_context import (
    fusion_reasons_of,
    verdict_transition_trace_of,
)
from arvis.kernel.pipeline.gate_overrides import GateOverrides

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline_context import (
        CognitivePipelineContext,
    )


def resolve_overrides(ctx: CognitivePipelineContext) -> GateOverrides:
    overrides = getattr(ctx, "gate_overrides", None)
    if overrides is not None:
        return cast(GateOverrides, overrides)

    # F-001: gate overrides are host-injected first-class context
    # state; the request-facing extra channel never carries them.
    return GateOverrides()


def initialize_context(ctx: CognitivePipelineContext) -> logging.Logger:
    """Gate-entry normalization of the scientific context.

    Campaign STRUCT (LOT S4): the historical version of this function
    hydrated the scientific sub-contexts from root-level legacy
    attributes. On the real, typed pipeline context every one of those
    reads went through the mirror properties, whose getters read the
    very scientific fields being written: the whole walk was an
    identity, kept alive by duck-typed test contexts that no longer
    exist. What remains is the real work: composite defaults and the
    compliance injection channel.
    """
    # Journal aliases (campaign OBS, LOT O2): the typed journal lists
    # are the storage; the extra keys expose the SAME list objects as
    # exports, so host-visible content stays byte-identical while
    # arvis code reads only the journal. The accessors adopt a
    # pre-seeded export list (direct compositions, tests) as storage
    # and install the export alias.
    fusion_reasons_of(ctx)
    verdict_transition_trace_of(ctx)

    composite = ctx.scientific.composite
    lyap = ctx.scientific.lyapunov

    if composite.delta_w_history is None:
        composite.delta_w_history = []
    if composite.w_current is None:
        composite.w_current = 0.0
    if composite.delta_w is None:
        composite.delta_w = 0.0

    # Bridge the per-state slow/symbolic channel (lyapunov context,
    # written by the core path and by hosts through the state
    # properties) into the pairwise composite slots the W evaluation
    # consumes. This was the one live copy inside the historical
    # hydration walk.
    if composite.prev_slow is None:
        composite.prev_slow = lyap.slow_state_prev
    if composite.cur_slow is None:
        composite.cur_slow = lyap.slow_state
    if composite.prev_symbolic is None:
        composite.prev_symbolic = lyap.symbolic_state_prev
    if composite.cur_symbolic is None:
        composite.cur_symbolic = lyap.symbolic_state

    # -----------------------------------------------------
    # Preserve injected compliance/runtime values (host extra
    # channel; see compliance/internal_invariants/scenarios).
    # -----------------------------------------------------
    if ctx.extra.get("preserve_injected_lyapunov", False):
        injected_delta = ctx.extra.get("delta_w")
        injected_stable = ctx.extra.get("stable")

        if injected_delta is not None:
            composite.delta_w = float(injected_delta)

        if injected_stable is not None:
            ctx.scientific.regime_state.stable = bool(injected_stable)

    return logging.getLogger(__name__)
