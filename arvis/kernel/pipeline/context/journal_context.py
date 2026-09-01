# arvis/kernel/pipeline/context/journal_context.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineJournalContext:
    """Typed storage of the run's cross-component signals and journal.

    Campaign OBS (LOT O2). Historically these values lived only as
    ``ctx.extra`` keys, which made the extra dict a hidden control-flow
    bus between gate components (and an accidental injection surface).
    The journal context is now the STORAGE arvis code reads; the extra
    keys remain as write-only EXPORTS for hosts, byte-identical to
    before (the accumulator lists are aliased into extra at gate entry,
    the scalars are dual-written at their historical sites).

    Doctrine: arvis code never READS these values from ``ctx.extra``;
    it reads them here (or from their canonical scientific/execution
    sub-context when one exists). The extra-read ratchet enforces this.
    """

    # ---- gate reason and trace accumulators (aliased into extra) ----
    fusion_reasons: list[str] = field(default_factory=list)
    verdict_transition_trace: list[dict[str, Any]] = field(default_factory=list)

    # ---- gate scalar signals (dual-written to extra) ----
    final_reason_codes: tuple[str, ...] = ()
    recovery_detected: bool = False
    hard_adaptive_veto: bool = False
    kappa_hard_block: bool = False
    # Gate-side adaptive band (distinct from the control stage's
    # ctx.kappa_band channel).
    kappa_band: str | None = None
    global_instability: bool = False
    global_instability_warning: bool = False
    switching_warning: bool = False
    exponential_bound_warning: bool = False
    low_confidence_escalation: bool = False
    projection_lyapunov_compatible: bool | None = None
    pi_structured_available: bool = False
    confirmation_override: bool = False
    # Declared input risk recorded by the input-risk gate (None once
    # sanitized); consumed by the tool authorization layer.
    input_risk: float | None = None

    # ---- verdict provenance ledger and gate fusion trace ----
    # (LOT O3: the last two cross-component structures to leave the
    # extra bus; the accessors below keep the exports aliased.)
    verdict_provenance: dict[str, str] = field(default_factory=dict)
    fusion_trace: dict[str, Any] | None = None


def journal_of(ctx: Any) -> PipelineJournalContext | None:
    """The context's journal, or None on partial duck contexts.

    Gate components are exercised by tolerance tests with minimal
    contexts; the journal dual-writes are guarded through this helper
    so those contracts keep holding (the extra export write remains
    the boundary behavior in that case).
    """
    return getattr(ctx, "journal", None)


def fusion_reasons_of(ctx: Any) -> list[Any]:
    """The run's fusion reasons accumulator.

    Real contexts: the journal list is the storage, and this accessor
    keeps the ``extra["fusion_reasons"]`` export aliased to the SAME
    list (adopting a pre-seeded export list on first touch, so direct
    compositions and tests that seed extra keep working). Partial duck
    contexts without a journal fall back to the historical extra list.
    """
    journal: PipelineJournalContext | None = getattr(ctx, "journal", None)
    if journal is not None:
        extra = getattr(ctx, "extra", None)
        if isinstance(extra, dict):
            exported = extra.get("fusion_reasons")
            if exported is not journal.fusion_reasons:
                if isinstance(exported, list) and not journal.fusion_reasons:
                    journal.fusion_reasons = exported
                extra["fusion_reasons"] = journal.fusion_reasons
        return journal.fusion_reasons
    extra = getattr(ctx, "extra", None)
    if isinstance(extra, dict):
        reasons = extra.setdefault("fusion_reasons", [])
        if isinstance(reasons, list):
            return reasons
    return []


def replace_fusion_reasons(ctx: Any, new_reasons: Any) -> list[Any]:
    """Replace the fusion reasons wholesale, in place.

    The gate has normalization and supersede steps that historically
    REASSIGNED ctx.extra["fusion_reasons"] to a fresh list; doing that
    would break the journal/export alias. Mutating in place keeps one
    list, visible identically through the journal and the export.
    """
    reasons = fusion_reasons_of(ctx)
    reasons[:] = list(new_reasons)
    extra = getattr(ctx, "extra", None)
    if isinstance(extra, dict):
        extra["fusion_reasons"] = reasons
    return reasons


def verdict_transition_trace_of(ctx: Any) -> list[Any]:
    """The run's verdict transition ledger, same aliasing contract as
    ``fusion_reasons_of``."""
    journal: PipelineJournalContext | None = getattr(ctx, "journal", None)
    if journal is not None:
        extra = getattr(ctx, "extra", None)
        if isinstance(extra, dict):
            exported = extra.get("verdict_transition_trace")
            if exported is not journal.verdict_transition_trace:
                if isinstance(exported, list) and not journal.verdict_transition_trace:
                    journal.verdict_transition_trace = exported
                extra["verdict_transition_trace"] = journal.verdict_transition_trace
        return journal.verdict_transition_trace
    extra = getattr(ctx, "extra", None)
    if isinstance(extra, dict):
        trace = extra.setdefault("verdict_transition_trace", [])
        if isinstance(trace, list):
            return trace
    return []


def verdict_provenance_of(ctx: Any) -> dict[str, str]:
    """The verdict provenance ledger, same aliasing contract as
    ``fusion_reasons_of`` (the export key is "verdict_provenance")."""
    journal: PipelineJournalContext | None = getattr(ctx, "journal", None)
    if journal is not None:
        extra = getattr(ctx, "extra", None)
        if isinstance(extra, dict):
            exported = extra.get("verdict_provenance")
            if exported is not journal.verdict_provenance:
                if isinstance(exported, dict) and not journal.verdict_provenance:
                    journal.verdict_provenance = exported
                extra["verdict_provenance"] = journal.verdict_provenance
        return journal.verdict_provenance
    extra = getattr(ctx, "extra", None)
    if isinstance(extra, dict):
        ledger = extra.setdefault("verdict_provenance", {})
        if isinstance(ledger, dict):
            return ledger
    return {}
