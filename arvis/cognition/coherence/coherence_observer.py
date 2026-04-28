# arvis/cognition/coherence/coherence_observer.py

from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any

from arvis.cognition.coherence.change_budget import ChangeBudget
from arvis.cognition.coherence.coherence_limits import (
    DEFAULT_MAX_CHANGES,
    DEFAULT_STEP_CAP,
)


@dataclass(frozen=True)
class CoherenceSignature:
    """
    Declarative signature extracted from a CognitiveBundleSnapshot.

    This is the "Z(t)" used to measure structural oscillation.
    Content-free: no user text, no reconstruction.
    """

    reason: str
    proposed_action_ids: set[str]
    memory_intent: str
    conflict_types: set[str]
    knowledge_state: str
    uncertainty_frame_ids: set[str]
    context_hint_keys: set[str]


class CoherenceObserver:
    """
    Passive observer computing a change metric between two bundles.

    - no inference
    - no enforcement
    - no execution
    """

    @staticmethod
    def signature(bundle: Any) -> CoherenceSignature:
        """
        Extract a declarative signature from a bundle-like object.

        Uses duck-typing to avoid tight coupling with DTO shapes.
        """
        decision = getattr(bundle, "decision_result", None)

        reason = str(getattr(decision, "reason", "") or "")

        # Actions: store by action_id if available, else stringify
        proposed_actions = getattr(decision, "proposed_actions", None) or []
        action_ids: set[str] = set()
        for a in proposed_actions:
            aid = getattr(a, "action_id", None)
            action_ids.add(str(aid if aid is not None else a))

        # Memory intent
        memory_intent = str(getattr(decision, "memory_intent", "") or "")

        # Conflicts: store by conflict.type if available
        conflicts = getattr(decision, "conflicts", None) or []
        conflict_types: set[str] = set()
        for c in conflicts:
            ctype = getattr(c, "type", None)
            conflict_types.add(str(ctype if ctype is not None else c))

        # Knowledge snapshot state
        ksnap = getattr(decision, "knowledge_snapshot", None)
        kstate = ""
        if ksnap is not None:
            kstate = str(getattr(ksnap, "state", "") or "")

        # Uncertainty frames: store by frame_id if available
        frames = getattr(decision, "uncertainty_frames", None) or []
        frame_ids: set[str] = set()
        for f in frames:
            fid = getattr(f, "frame_id", None)
            frame_ids.add(str(fid if fid is not None else f))

        # Context hints keys only (no values)
        ctx_hints = getattr(bundle, "context_hints", None)
        if ctx_hints is None and decision is not None:
            ctx_hints = getattr(decision, "context_hints", None)
        ctx_hints = ctx_hints or {}
        hint_keys = set(map(str, ctx_hints.keys()))

        return CoherenceSignature(
            reason=reason,
            proposed_action_ids=action_ids,
            memory_intent=memory_intent,
            conflict_types=conflict_types,
            knowledge_state=kstate,
            uncertainty_frame_ids=frame_ids,
            context_hint_keys=hint_keys,
        )

    @staticmethod
    def distance(curr: CoherenceSignature, prev: CoherenceSignature) -> int:
        """
        Declarative change distance d(Z(t), Z(t-1)).

        Counts structural changes. No content.
        """
        delta = 0

        # Reason change (categorical trace)
        delta += 1 if curr.reason != prev.reason else 0

        # Symmetric differences on sets
        delta += len(
            curr.proposed_action_ids.symmetric_difference(prev.proposed_action_ids)
        )
        delta += 1 if curr.memory_intent != prev.memory_intent else 0
        delta += len(curr.conflict_types.symmetric_difference(prev.conflict_types))
        delta += 1 if curr.knowledge_state != prev.knowledge_state else 0
        delta += len(
            curr.uncertainty_frame_ids.symmetric_difference(prev.uncertainty_frame_ids)
        )
        delta += len(
            curr.context_hint_keys.symmetric_difference(prev.context_hint_keys)
        )

        return int(delta)

    @staticmethod
    def update_budget(
        *,
        previous_bundle: Any | None,
        current_bundle: Any,
        previous_budget: ChangeBudget | None = None,
        max_changes: int = DEFAULT_MAX_CHANGES,
        step_cap: int = DEFAULT_STEP_CAP,
        timestamp: int | None = None,
    ) -> ChangeBudget:
        """
        Compute distance between bundles and increment ChangeBudget.

        If previous_bundle is None, delta=0 (first cycle).
        """
        if timestamp is None:
            timestamp = int(time())

        if previous_budget is None:
            previous_budget = ChangeBudget(
                max_changes=max_changes,
                current_changes=0,
                timestamp=timestamp,
            )

        if previous_bundle is None:
            return ChangeBudget(
                max_changes=previous_budget.max_changes,
                current_changes=previous_budget.current_changes,
                timestamp=timestamp,
            )

        prev_sig = CoherenceObserver.signature(previous_bundle)
        curr_sig = CoherenceObserver.signature(current_bundle)

        d = CoherenceObserver.distance(curr_sig, prev_sig)
        d_capped = min(int(d), int(step_cap))

        return ChangeBudget(
            max_changes=previous_budget.max_changes,
            current_changes=int(previous_budget.current_changes) + d_capped,
            timestamp=timestamp,
        )
