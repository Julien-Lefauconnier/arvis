# arvis/errors/redaction.py

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from arvis.errors.types import ErrorPayload, ErrorPayloadValue

REDACTED: Final[str] = "<redacted>"

DEFAULT_SENSITIVE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "cookie",
        "password",
        "secret",
        "token",
        "api_key",
        "access_key",
        "private_key",
        "traceback",
    }
)

DEFAULT_SENSITIVE_FRAGMENTS: Final[tuple[str, ...]] = (
    "token",
    "secret",
    "password",
    "credential",
    "authorization",
    "cookie",
    "private_key",
    "access_key",
    "api_key",
    "bearer",
    "traceback",
)


def redact_error_payload(
    payload: ErrorPayload,
    *,
    include_traceback: bool = False,
    include_error_id: bool = True,
    sensitive_keys: frozenset[str] = DEFAULT_SENSITIVE_KEYS,
    sensitive_fragments: tuple[str, ...] = DEFAULT_SENSITIVE_FRAGMENTS,
) -> ErrorPayload:
    """
    Return a safe, serializable error payload.

    Rules:
    - traceback is excluded unless explicitly requested
    - error_id may be excluded for public/API payloads
    - sensitive nested keys are redacted recursively
    - fingerprint is preserved for deterministic deduplication
    """
    out = _redact_mapping(
        payload,
        include_traceback=include_traceback,
        sensitive_keys=sensitive_keys,
        sensitive_fragments=sensitive_fragments,
    )

    if not include_traceback:
        out.pop("traceback", None)

    if not include_error_id:
        out.pop("error_id", None)

    return out


def _redact_mapping(
    value: Mapping[str, ErrorPayloadValue],
    *,
    include_traceback: bool,
    sensitive_keys: frozenset[str],
    sensitive_fragments: tuple[str, ...],
) -> dict[str, ErrorPayloadValue]:
    out: dict[str, ErrorPayloadValue] = {}

    for key, item in value.items():
        key_lower = key.lower()

        if key_lower == "traceback" and not include_traceback:
            continue

        is_sensitive_fragment = any(
            fragment in key_lower for fragment in sensitive_fragments
        )

        if key_lower in sensitive_keys:
            out[key] = REDACTED
            continue

        if is_sensitive_fragment:
            out[key] = REDACTED
            continue

        out[key] = _redact_value(
            item,
            include_traceback=include_traceback,
            sensitive_keys=sensitive_keys,
            sensitive_fragments=sensitive_fragments,
        )

    return out


def _redact_value(
    value: ErrorPayloadValue,
    *,
    include_traceback: bool,
    sensitive_keys: frozenset[str],
    sensitive_fragments: tuple[str, ...],
) -> ErrorPayloadValue:
    if isinstance(value, dict):
        return _redact_mapping(
            value,
            include_traceback=include_traceback,
            sensitive_keys=sensitive_keys,
            sensitive_fragments=sensitive_fragments,
        )

    if isinstance(value, list):
        return [
            _redact_value(
                item,
                include_traceback=include_traceback,
                sensitive_keys=sensitive_keys,
                sensitive_fragments=sensitive_fragments,
            )
            for item in value
        ]

    return value
