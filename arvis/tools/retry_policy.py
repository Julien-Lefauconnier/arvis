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

        # --- respect tool spec if present ---
        last_tool = getattr(ctx, "_last_tool_spec", None)
        if last_tool is not None:
            if not last_tool.retryable:
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
