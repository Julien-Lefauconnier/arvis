# arvis/kernel/pipeline/stages/runtime_stage.py

from __future__ import annotations

from typing import Any


class RuntimeStage:
    def run(self, pipeline: Any, ctx: Any) -> None:
        try:
            runtime = getattr(ctx, "control_runtime", None)
            if runtime is None:
                getter = getattr(pipeline, "_get_control_runtime", None)
                if callable(getter):
                    runtime = getter(ctx.user_id)
                    ctx.control_runtime = runtime

            if runtime is not None:
                runtime.last_risk = float(ctx.collapse_risk)
                runtime.inertia_risk = float(ctx.collapse_risk)
                runtime.last_action = str(getattr(ctx.action_decision, "mode", None))

        except Exception:
            pass

        # -----------------------------------------
        #  Switching runtime
        # -----------------------------------------
        try:
            switching_runtime = getattr(ctx, "switching_runtime", None)
            regime = getattr(ctx, "regime", None)

            if switching_runtime is not None and regime is not None:
                switching_runtime.update(str(regime))
        except Exception:
            pass

        # -----------------------------------------
        # Global stability observer
        # -----------------------------------------
        try:
            observer = getattr(pipeline, "global_stability_observer", None)
            if observer:
                metrics = observer.update(ctx)
                ctx.global_stability_metrics = metrics
        except Exception:
            ctx.global_stability_metrics = None
