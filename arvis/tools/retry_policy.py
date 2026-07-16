# arvis/tools/retry_policy.py

from typing import Any


class ToolRetryPolicy:
    """
    Stateless retry decision logic.

    ZKCS-safe:
    - no execution
    - no side effects
    """

    def evaluate(self, ctx: Any) -> None:
        if not getattr(ctx, "_tool_failure", False):
            return

        # --- respect tool spec (F-016: retry requires idempotence) ---
        last_tool = getattr(ctx, "_last_tool_spec", None)
        if last_tool is None:
            # Unknown effect semantics: an automatic replay could
            # re-fire a non-idempotent effect, so no spec means no
            # automatic retry (fail-closed). The explicit host retry
            # channel is unaffected.
            return
        if not last_tool.retryable:
            return
        if last_tool.side_effectful and not last_tool.idempotent:
            # F-016: a side-effectful, non-idempotent effect is never
            # replayed automatically (double e-mail, double payment).
            return

        # retry only if system is safe enough
        risk = float(getattr(ctx, "collapse_risk", 0.0))

        if risk > 0.6:
            return

        runtime_policy = getattr(ctx, "runtime_policy", None)

        retries = (
            runtime_policy.retry_count
            if runtime_policy is not None
            else int(ctx.extra.get("tool_retry_count", 0))
        )

        if retries >= 2:
            return

        # inject retry signal
        if runtime_policy is not None:
            runtime_policy.retry_requested = True
            runtime_policy.retry_count = retries + 1
