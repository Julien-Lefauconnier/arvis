# arvis/math/projection/pi_operator.py

from __future__ import annotations

from typing import Any

from arvis.math.projection.projection_view import ProjectionView


class PiOperator:
    """
    Projection operator Π:
    Projects a state into a safe / stable domain.
    """

    def project(
        self,
        state: ProjectionView,
        ctx: Any = None,
    ) -> ProjectionView:
        if state is None:
            return ProjectionView(_values={})

        projected: dict[str, float] = {}

        # -----------------------------------------
        # Context-aware parameters
        # -----------------------------------------
        adaptive_ctx = getattr(getattr(ctx, "scientific", None), "adaptive", None)
        regime = getattr(
            getattr(adaptive_ctx, "adaptive_snapshot", None), "regime", "stable"
        )
        validity = getattr(
            getattr(adaptive_ctx, "validity_envelope", None), "valid", True
        )

        # Projection strength. Driven by the validity envelope and
        # the adaptive regime, and by nothing else.
        #
        # A "stability feedback control" block used to clamp alpha to
        # 0.6 whenever the private ctx._dv attribute was positive,
        # reading it as a signed energy derivative. That attribute
        # carries float(core_ctx.drift_score), a DriftSignal magnitude
        # clamped to [0, 1] and never negative, so the clamp fired on
        # every turn with any drift at all and this light branch was
        # reachable only at exactly zero drift (campaign PROJ, DM-P1;
        # same misread as the certificate defect campaign ALLOW
        # closed). The signal the block wanted does not exist at
        # projection time; drift-reactive projection strength is
        # re-posed at DM4 with a real signal.
        if not validity:
            alpha = 0.5  # aggressive projection
        elif regime == "critical":
            alpha = 0.7  # moderate
        else:
            alpha = 1.0  # light (identity up to the final squash)

        for k, v in state.items():
            # -----------------------------------------
            # Ignore non-numeric values (strict contract)
            # -----------------------------------------
            if not isinstance(v, (int, float)) or v != v:
                continue

            v = float(v)

            # -----------------------------------------
            # Smooth projection instead of hard clip
            # -----------------------------------------
            v_proj = v / (1.0 + abs(v))

            # -----------------------------------------
            # Adaptive blending:
            # keep a share of original value, contract the rest
            # -----------------------------------------
            blended = alpha * v + (1.0 - alpha) * v_proj

            # -----------------------------------------
            # FINAL SAFETY PROJECTION (kernel invariant)
            # -----------------------------------------
            projected[k] = blended / (1.0 + abs(blended))

        return ProjectionView(_values=projected)
