# arvis/kernel/pipeline/stages/gate_stage.py

from __future__ import annotations

from typing import Any
from arvis.math.lyapunov.lyapunov_gate import (
    lyapunov_gate,
    LyapunovVerdict,
    LyapunovGateParams,
)
from arvis.math.control.eps_adaptive import CognitiveMode
from arvis.cognition.control.cognitive_control_snapshot import CognitiveControlSnapshot


class GateStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        HIGH_RISK_THRESHOLD = 0.8

        # -----------------------------------------
        # 1. VERDICT COMPUTATION
        # -----------------------------------------
        if ctx.stable is False:
            verdict = LyapunovVerdict.ABSTAIN

        elif float(ctx.collapse_risk) >= HIGH_RISK_THRESHOLD:
            verdict = LyapunovVerdict.ABSTAIN

        elif ctx._cognitive_mode == CognitiveMode.CRITICAL:
            verdict = LyapunovVerdict.ABSTAIN

        elif ctx.cur_lyap is None:
            verdict = LyapunovVerdict.REQUIRE_CONFIRMATION

        else:
            previous = ctx.prev_lyap or ctx.cur_lyap

            params = LyapunovGateParams(
                eps_override=ctx._epsilon
            )

            verdict = lyapunov_gate(
                previous=previous,
                current=ctx.cur_lyap,
                params=params,
            )

        # -----------------------------------------
        # 2. ENRICH CONTROL SNAPSHOT
        # -----------------------------------------
        base = ctx.control_snapshot

        ctx.control_snapshot = CognitiveControlSnapshot(
            gate_mode=base.gate_mode,
            epsilon=base.epsilon,
            smoothed_risk=base.smoothed_risk,
            lyap_verdict=verdict,
            exploration=base.exploration,
            drift=base.drift,
            regime=base.regime,
            calibration=base.calibration,
            temporal_pressure=ctx.temporal_pressure,
            temporal_modulation=ctx.temporal_modulation,
        )

        # -----------------------------------------
        # 3. EXPORT
        # -----------------------------------------
        ctx.gate_result = verdict