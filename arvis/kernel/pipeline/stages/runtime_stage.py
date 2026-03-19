# arvis/kernel/pipeline/stages/runtime_stage.py

from __future__ import annotations

from typing import Any

class RuntimeStage:

    def run(self, pipeline: Any, ctx: Any) -> None:

        try:
            runtime = ctx.control_runtime

            runtime.last_risk = float(ctx.collapse_risk)
            runtime.inertia_risk = float(ctx.collapse_risk)

            runtime.last_action = str(
                getattr(ctx.action_decision, "mode", None)
            )

        except Exception:
            # volontairement silencieux → non bloquant
            pass