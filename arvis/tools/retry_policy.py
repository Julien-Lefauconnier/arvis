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

        # retry only if system is safe enough
        risk = float(getattr(ctx, "collapse_risk", 0.0))

        if risk > 0.6:
            return

        retries = ctx.extra.get("tool_retry_count", 0)

        if retries >= 2:
            return

        # inject retry signal
        ctx.extra.setdefault("execution_policy", {})
        ctx.extra["execution_policy"]["retry"] = True

        # backward compatibility (temp)
        ctx.extra["retry_tool"] = True
        ctx.extra["tool_retry_count"] = retries + 1