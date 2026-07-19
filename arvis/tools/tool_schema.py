"""Shared fail-closed JSON-schema validation for tool boundaries."""

from __future__ import annotations

from typing import Any

import jsonschema


def schema_violation(instance: Any, schema: dict[str, Any]) -> str | None:
    """Return a structural violation path, or ``None`` when valid."""
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(part) for part in exc.absolute_path)
        return path or "<root>"
    except jsonschema.SchemaError:
        return "<invalid_schema>"
    return None


__all__ = ["schema_violation"]
