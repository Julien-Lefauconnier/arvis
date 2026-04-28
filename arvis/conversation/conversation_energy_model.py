# arvis/conversation/conversation_energy_model.py


class ConversationEnergyModel:
    """
    Aggregates multiple cognitive signals into a single
    conversational energy score.

    This helps detect unstable conversational regimes earlier
    than collapse-only guards.
    """

    # --------------------------------------------------
    # DYNAMIC WEIGHTS (adaptive, normalized)
    # --------------------------------------------------
    _dynamic_weights: dict[str, float] = {
        "collapse": 0.4,
        "uncertainty": 0.25,
        "pressure": 0.15,
        "memory": 0.1,
        "constraint": 0.1,
    }

    @staticmethod
    def compute_energy(
        *,
        collapse_risk: float | None,
        uncertainty: float | None,
        temporal_pressure: float | None,
        memory_pressure: float | None = None,
        has_constraints: bool | None = None,
        delta_v: float | None = None,
        delta_w: float | None = None,
        dynamic_weights: dict[str, float] | None = None,
    ) -> float:
        collapse = collapse_risk if collapse_risk is not None else 0.0
        uncertainty_val = uncertainty if uncertainty is not None else 0.0
        pressure = temporal_pressure if temporal_pressure is not None else 0.0
        memory = memory_pressure if memory_pressure is not None else 0.0
        constraint = 1.0 if has_constraints else 0.0
        dv = delta_v if delta_v is not None else 0.0
        dw = delta_w if delta_w is not None else 0.0

        w = dynamic_weights or ConversationEnergyModel._dynamic_weights

        # ensure all keys exist
        w = {
            "collapse": w.get("collapse", 0.0),
            "uncertainty": w.get("uncertainty", 0.0),
            "pressure": w.get("pressure", 0.0),
            "memory": w.get("memory", 0.0),
            "constraint": w.get("constraint", 0.0),
            "delta_v": w.get("delta_v", 0.1),
            "delta_w": w.get("delta_w", 0.0),
        }

        # normalize weights (safety)
        total = sum(w.values())
        if total > 0:
            w = {k: v / total for k, v in w.items()}

        # -----------------------------------------
        # ΔV contribution (only divergence matters)
        # -----------------------------------------
        # Only divergence contributes (ΔV > 0)
        # and clamping to avoid energy explosion
        dv_contrib = min(max(dv, 0.0), 1.0)
        dw_contrib = min(max(dw, 0.0), 1.0)

        energy = (
            w["collapse"] * collapse
            + w["uncertainty"] * uncertainty_val
            + w["pressure"] * pressure
            + w["memory"] * memory
            + w["constraint"] * constraint
            + w["delta_v"] * dv_contrib
            + w["delta_w"] * dw_contrib
        )

        return min(max(energy, 0.0), 1.0)
