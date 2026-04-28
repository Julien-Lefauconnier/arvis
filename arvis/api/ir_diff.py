# arvis/api/ir_diff.py

from __future__ import annotations

from typing import Any


def diff_ir(old: dict[str, Any], new: dict[str, Any]) -> dict[str, tuple[Any, Any]]:
    """
    Compute a structural diff between two IR objects.

    Returns:
        {
            "path.to.field": (old_value, new_value)
        }
    """

    diffs: dict[str, tuple[Any, Any]] = {}

    def _walk(o: Any, n: Any, path: str) -> None:
        if type(o) is not type(n):
            diffs[path] = (o, n)
            return

        if isinstance(o, dict):
            keys = set(o.keys()) | set(n.keys())
            for k in keys:
                _walk(
                    o.get(k),
                    n.get(k),
                    f"{path}.{k}" if path else k,
                )
            return

        if isinstance(o, list):
            if o != n:
                diffs[path] = (o, n)
            return

        if o != n:
            diffs[path] = (o, n)

    _walk(old, new, "")

    return diffs
