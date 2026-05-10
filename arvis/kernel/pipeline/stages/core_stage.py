# arvis/kernel/pipeline/stages/core_stage.py

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import numpy as np

from arvis.math.core.fast_dynamics import FastDynamicsSnapshot
from arvis.math.core.perturbation import compute_perturbation
from arvis.math.lyapunov.lyapunov import LyapunovState, lyapunov_value
from arvis.math.lyapunov.quadratic_lyapunov import QuadraticLyapunovSnapshot
from arvis.math.lyapunov.quadratic_projection import project_operational_to_quadratic
from arvis.math.lyapunov.slow_dynamics import update_slow_state
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.lyapunov.target_map import target_map
from arvis.math.signals import DriftSignal, RiskSignal


class CoreStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        # ==========================================================
        # Transitional compatibility layer
        # ----------------------------------------------------------
        # Old tests and legacy runtime contexts may not yet expose
        # the structured scientific namespaces.
        #
        # During migration we lazily create them to preserve
        # backward compatibility with the flat context API.
        # ==========================================================

        if not hasattr(ctx, "scientific"):
            ctx.scientific = SimpleNamespace(
                core=SimpleNamespace(),
                lyapunov=SimpleNamespace(
                    prev_lyap=None,
                    cur_lyap=None,
                    prev_quadratic_lyap_state=None,
                    cur_quadratic_lyap_state=None,
                    quadratic_lyap_snapshot=None,
                    quadratic_comparability=None,
                    slow_state=None,
                    slow_state_prev=None,
                    symbolic_state=None,
                    symbolic_state_prev=None,
                ),
                regime_state=SimpleNamespace(
                    regime=None,
                    stable=None,
                    fast_dynamics=None,
                    perturbation=None,
                    theoretical_regime=None,
                ),
                switching=SimpleNamespace(
                    switching_params=None,
                ),
                adaptive=SimpleNamespace(),
                composite=SimpleNamespace(),
            )

        scientific = ctx.scientific
        core_ctx = scientific.core
        lyap_ctx = scientific.lyapunov
        regime_ctx = scientific.regime_state
        switching_ctx = scientific.switching

        bundle = ctx.decision_layer.bundle

        # -----------------------------------------
        # 0. Preserve previous causal states
        # -----------------------------------------
        # The pipeline owns causal history.
        # The core only produces the current state.
        preserve_injected = bool(
            getattr(ctx, "extra", {}).get("preserve_injected_lyapunov", False)
        )
        injected_prev = lyap_ctx.prev_lyap
        injected_cur = lyap_ctx.cur_lyap
        prev_slow_before = lyap_ctx.slow_state
        prev_symbolic_before = lyap_ctx.symbolic_state
        prev_lyap_before = (
            injected_prev
            if preserve_injected and injected_prev is not None
            else injected_cur
        )

        # -----------------------------------------
        # 1. Core processing
        # -----------------------------------------
        scientific_snapshot = pipeline.core.process(bundle)
        core_ctx.scientific_snapshot = scientific_snapshot

        core_snapshot = (
            getattr(scientific_snapshot, "core_snapshot", None) or scientific_snapshot
        )

        core_ctx.collapse_risk = RiskSignal(
            getattr(scientific_snapshot, "collapse_risk", 0.0) or 0.0
        )

        # -----------------------------------------
        # 2. Lyapunov states
        # -----------------------------------------

        new_cur = getattr(scientific_snapshot, "cur_lyap", None) or getattr(
            core_snapshot, "cur_lyap", None
        )

        def _normalize_lyap(x: Any) -> LyapunovState | None:
            if x is None:
                return None
            if isinstance(x, LyapunovState):
                return x
            return LyapunovState.from_scalar(x)

        new_cur = _normalize_lyap(new_cur)

        # -----------------------------------------
        # Compliance / injected-state preservation
        # -----------------------------------------
        if preserve_injected and injected_cur is not None and new_cur is None:
            new_cur = injected_cur

        # Causal convention:
        # prev = last cycle current, cur = current cycle current
        lyap_ctx.prev_lyap = prev_lyap_before
        lyap_ctx.cur_lyap = new_cur

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

            regime_ctx.fast_dynamics = FastDynamicsSnapshot(
                regime=str(
                    getattr(regime_ctx.theoretical_regime, "q_t", None)
                    or regime_ctx.regime
                ),
                x_prev=x_prev,
                x_next=x_next,
                delta_norm=delta_norm,
            )

        except Exception:
            regime_ctx.fast_dynamics = None

        # -----------------------------------------
        # Paper-aligned quadratic fast state
        # -----------------------------------------
        prev_q = lyap_ctx.cur_quadratic_lyap_state
        cur_q = project_operational_to_quadratic(lyap_ctx.cur_lyap)

        lyap_ctx.prev_quadratic_lyap_state = prev_q
        lyap_ctx.cur_quadratic_lyap_state = cur_q

        try:
            regime_name = str(
                getattr(regime_ctx.theoretical_regime, "q_t", None)
                or regime_ctx.regime
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

                lyap_ctx.quadratic_lyap_snapshot = QuadraticLyapunovSnapshot(
                    regime=regime_name,
                    value=q_value,
                    delta=q_delta,
                    dimension=len(cur_q.as_vector()),
                )
            else:
                lyap_ctx.quadratic_lyap_snapshot = None
        except Exception:
            lyap_ctx.quadratic_lyap_snapshot = None

        try:
            lyap_ctx.quadratic_comparability = getattr(
                pipeline, "quadratic_comparability", None
            )
        except Exception:
            lyap_ctx.quadratic_comparability = None

        # If no current Lyapunov state is available, the gate must not
        # fabricate a causal transition.
        if lyap_ctx.cur_lyap is None:
            regime_ctx.stable = False

        core_ctx.drift_score = DriftSignal(
            getattr(scientific_snapshot, "drift_score", None)
            or getattr(scientific_snapshot, "dv", None)
            or getattr(core_snapshot, "drift_score", None)
            or getattr(core_snapshot, "dv", 0.0)
            or 0.0
        )

        try:
            ctx._dv = float(core_ctx.drift_score)
        except Exception:
            ctx._dv = 0.0

        regime_ctx.regime = getattr(
            scientific_snapshot,
            "regime",
            None,
        ) or getattr(core_snapshot, "regime", None)

        regime_ctx.stable = (
            getattr(scientific_snapshot, "stable", None)
            if getattr(scientific_snapshot, "stable", None) is not None
            else getattr(core_snapshot, "stable", None)
        )

        try:
            reflexive = getattr(scientific_snapshot, "reflexive_state", None)

            if reflexive:
                new_slow = SlowState(
                    stability_memory=float(
                        reflexive.get("stability_memory", 0.0) or 0.0
                    ),
                    structural_risk=float(reflexive.get("structural_risk", 0.0) or 0.0),
                    regime_persistence=float(
                        reflexive.get("regime_persistence", 0.0) or 0.0
                    ),
                    uncertainty_drift=float(
                        reflexive.get("uncertainty_drift", 0.0) or 0.0
                    ),
                )
            else:
                new_slow = SlowState.zero()
        except Exception:
            new_slow = None

        # -----------------------------------------
        # 3. Causal export for composite gate
        # -----------------------------------------
        lyap_ctx.slow_state_prev = prev_slow_before

        # -----------------------------------------
        # Future: slow-fast consistency (paper alignment)
        # Currently disabled (safe mode)
        # -----------------------------------------
        lyap_ctx.slow_state = new_slow

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
                symbolic_for_T = lyap_ctx.symbolic_state

                if symbolic_for_T is not None:
                    T_x = target_map(
                        symbolic_for_T,
                        fast=lyap_ctx.cur_lyap,
                    )
                else:
                    T_x = np.zeros_like(prev_slow_before.as_vector(), dtype=float)

                eta = 0.05
                if switching_ctx.switching_params is not None:
                    eta = float(
                        getattr(
                            switching_ctx.switching_params,
                            "eta",
                            0.05,
                        )
                    )

                lyap_ctx.slow_state = update_slow_state(
                    prev_slow_before,
                    T_x,
                    eta=eta,
                )
        except Exception:
            pass

        # Example future activation:
        # if prev_slow_before is not None and ctx.cur_lyap is not None:
        #     T_x = target_map(ctx.symbolic_state, ctx.cur_lyap)
        #     lyap_ctx.slow_state = update_slow_state(prev_slow_before, T_x)

        lyap_ctx.symbolic_state_prev = prev_symbolic_before

        # Current symbolic state is not produced by the core here.
        # It may be attached later by observability or another stage.
        # Keep whatever current value already exists, but do not fabricate it.
        lyap_ctx.symbolic_state = lyap_ctx.symbolic_state

        # -----------------------------------------
        #  perturbation w_t
        # -----------------------------------------
        try:
            regime_ctx.perturbation = compute_perturbation(ctx)
        except Exception:
            regime_ctx.perturbation = None

        # ==========================================================
        # Legacy flat-context compatibility bridge
        # ----------------------------------------------------------
        # Temporary during scientific namespace migration.
        # ==========================================================

        ctx.prev_lyap = lyap_ctx.prev_lyap
        ctx.cur_lyap = lyap_ctx.cur_lyap

        ctx.prev_quadratic_lyap_state = lyap_ctx.prev_quadratic_lyap_state
        ctx.cur_quadratic_lyap_state = lyap_ctx.cur_quadratic_lyap_state

        ctx.quadratic_lyap_snapshot = lyap_ctx.quadratic_lyap_snapshot
        ctx.quadratic_comparability = lyap_ctx.quadratic_comparability

        ctx.slow_state = lyap_ctx.slow_state
        ctx.slow_state_prev = lyap_ctx.slow_state_prev

        ctx.symbolic_state = lyap_ctx.symbolic_state
        ctx.symbolic_state_prev = lyap_ctx.symbolic_state_prev

        ctx.fast_dynamics = regime_ctx.fast_dynamics
        ctx.perturbation = regime_ctx.perturbation
        ctx.regime = regime_ctx.regime
        ctx.stable = regime_ctx.stable

        ctx.drift_score = core_ctx.drift_score
        ctx.collapse_risk = core_ctx.collapse_risk
