# arvis/kernel/pipeline/stages/core_stage.py

from __future__ import annotations

from typing import Any, Optional
import numpy as np

from arvis.math.signals import RiskSignal, DriftSignal
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.lyapunov import lyapunov_value
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.lyapunov.quadratic_projection import project_operational_to_quadratic
from arvis.math.lyapunov.quadratic_lyapunov import QuadraticLyapunovSnapshot
from arvis.math.core.fast_dynamics import FastDynamicsSnapshot
from arvis.math.core.perturbation import compute_perturbation
from arvis.math.lyapunov.target_map import target_map
from arvis.math.lyapunov.slow_dynamics import update_slow_state


class CoreStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        bundle = ctx.bundle

        # -----------------------------------------
        # 0. Preserve previous causal states
        # -----------------------------------------
        # The pipeline owns causal history.
        # The core only produces the current state.
        prev_slow_before = getattr(ctx, "slow_state", None)
        prev_symbolic_before = getattr(ctx, "symbolic_state", None)
        prev_lyap_before = getattr(ctx, "cur_lyap", None)

        # -----------------------------------------
        # 1. Core processing
        # -----------------------------------------
        scientific = pipeline.core.process(bundle)
        ctx.scientific_snapshot = scientific

        core_snapshot = getattr(scientific, "core_snapshot", None) or scientific

        ctx.collapse_risk = RiskSignal(
            getattr(scientific, "collapse_risk", 0.0) or 0.0
        )

        # -----------------------------------------
        # 2. Lyapunov states
        # -----------------------------------------

        new_cur = (
            getattr(scientific, "cur_lyap", None)
            or getattr(core_snapshot, "cur_lyap", None)
        )

        def _normalize_lyap(x: Any) -> Optional[LyapunovState]:
            if x is None:
                return None
            if isinstance(x, LyapunovState):
                return x
            return LyapunovState.from_scalar(x)


        new_cur = _normalize_lyap(new_cur)

        # Causal convention:
        # prev = last cycle current, cur = current cycle current
        ctx.prev_lyap = prev_lyap_before
        ctx.cur_lyap = new_cur

        # -----------------------------------------
        # fast dynamics snapshot
        # -----------------------------------------
        try:
            x_prev = prev_lyap_before
            x_next = new_cur

            delta_norm = None

            if x_prev is not None and x_next is not None:
                try:
                    delta_norm = abs(
                        float(lyapunov_value(x_next) - lyapunov_value(x_prev))
                    )
                except Exception:
                    delta_norm = None

            ctx.fast_dynamics = FastDynamicsSnapshot(
                regime=str(
                    getattr(getattr(ctx, "theoretical_regime", None), "q_t", None)
                    or ctx.regime
                ),
                x_prev=x_prev,
                x_next=x_next,
                delta_norm=delta_norm,
            )

        except Exception:
            ctx.fast_dynamics = None

        # -----------------------------------------
        # Paper-aligned quadratic fast state
        # -----------------------------------------
        prev_q = getattr(ctx, "cur_quadratic_lyap_state", None)
        cur_q = project_operational_to_quadratic(ctx.cur_lyap)

        ctx.prev_quadratic_lyap_state = prev_q
        ctx.cur_quadratic_lyap_state = cur_q

        try:
            regime_name = str(
                getattr(getattr(ctx, "theoretical_regime", None), "q_t", None)
                or ctx.regime
                or "transition"
            )
            family = getattr(pipeline, "quadratic_lyapunov_family", None)

            if family is not None and cur_q is not None:
                if not family.has_regime(regime_name):
                    regime_name = "transition"

                q_value = family.value(regime_name, cur_q)
                q_delta = None

                if prev_q is not None:
                    q_delta = family.delta(regime_name, prev_q, cur_q)

                ctx.quadratic_lyap_snapshot = QuadraticLyapunovSnapshot(
                    regime=regime_name,
                    value=q_value,
                    delta=q_delta,
                    dimension=len(cur_q.as_vector()),
                )
            else:
                ctx.quadratic_lyap_snapshot = None
        except Exception:
            ctx.quadratic_lyap_snapshot = None
        
        try:
            ctx.quadratic_comparability = getattr(pipeline, "quadratic_comparability", None)
        except Exception:
            ctx.quadratic_comparability = None

        # If no current Lyapunov state is available, the gate must not
        # fabricate a causal transition.
        if ctx.cur_lyap is None:
            ctx.stable = False

        ctx.drift_score = DriftSignal(
            getattr(scientific, "drift_score", None)
            or getattr(scientific, "dv", None)
            or getattr(core_snapshot, "drift_score", None)
            or getattr(core_snapshot, "dv", 0.0)
            or 0.0
        )

        ctx.regime = (
            getattr(scientific, "regime", None)
            or getattr(core_snapshot, "regime", None)
        )

        ctx.stable = (
            getattr(scientific, "stable", None)
            if getattr(scientific, "stable", None) is not None
            else getattr(core_snapshot, "stable", None)
        )

        try:
            reflexive = getattr(scientific, "reflexive_state", None)

            if reflexive:
                new_slow = SlowState(
                    stability_memory=float(reflexive.get("stability_memory", 0.0) or 0.0),
                    structural_risk=float(reflexive.get("structural_risk", 0.0) or 0.0),
                    regime_persistence=float(reflexive.get("regime_persistence", 0.0) or 0.0),
                    uncertainty_drift=float(reflexive.get("uncertainty_drift", 0.0) or 0.0),
                )
            else:
                new_slow = SlowState.zero()
        except Exception:
            new_slow = None


        # -----------------------------------------
        # 3. Causal export for composite gate
        # -----------------------------------------
        ctx.slow_state_prev = prev_slow_before
        
        # -----------------------------------------
        # Future: slow-fast consistency (paper alignment)
        # Currently disabled (safe mode)
        # -----------------------------------------
        ctx.slow_state = new_slow

        # -----------------------------------------
        # Optional paper-aligned slow dynamics
        # z_{t+1} = (1-eta) z_t + eta T(x_t)
        # -----------------------------------------
        try:
            if (
                getattr(ctx, "use_paper_slow_dynamics", False)
                and prev_slow_before is not None
                and ctx.cur_lyap is not None
            ):
                symbolic_for_T = getattr(ctx, "symbolic_state", None)

                if symbolic_for_T is not None:
                    T_x = target_map(symbolic_for_T, fast=ctx.cur_lyap)
                else:
                    T_x = np.zeros_like(prev_slow_before.as_vector(), dtype=float)

                eta = 0.05
                if getattr(ctx, "switching_params", None) is not None:
                    eta = float(getattr(ctx.switching_params, "eta", 0.05))

                ctx.slow_state = update_slow_state(
                    prev_slow_before,
                    T_x,
                    eta=eta,
                )
        except Exception:
            pass

        # Example future activation:
        # if prev_slow_before is not None and ctx.cur_lyap is not None:
        #     T_x = target_map(ctx.symbolic_state, ctx.cur_lyap)
        #     ctx.slow_state = update_slow_state(prev_slow_before, T_x)

        ctx.symbolic_state_prev = prev_symbolic_before
        
        # Current symbolic state is not produced by the core here.
        # It may be attached later by observability or another stage.
        # Keep whatever current value already exists, but do not fabricate it.
        ctx.symbolic_state = getattr(ctx, "symbolic_state", None)

        # -----------------------------------------
        #  perturbation w_t
        # -----------------------------------------
        try:
            ctx.perturbation = compute_perturbation(ctx)
        except Exception:
            ctx.perturbation = None