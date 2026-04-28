# arvis/api/version.py

from __future__ import annotations

import hashlib
import inspect
from importlib.metadata import PackageNotFoundError, version
from typing import Any

# -----------------------------------------------------
# Installed package version
# -----------------------------------------------------
try:
    PACKAGE_VERSION = version("arvis")
except PackageNotFoundError:
    PACKAGE_VERSION = "0.0.0-dev"


# -----------------------------------------------------
# EXISTING TEST CONTRACT
# -----------------------------------------------------
API_VERSION = "1.0.0"


# -----------------------------------------------------
# New short fingerprint (optional modern export)
# -----------------------------------------------------
def compute_public_api_fingerprint() -> str:
    try:
        import arvis.api as api

        exported = getattr(api, "__all__", None)
        if not exported:
            raise RuntimeError

        rows: list[str] = []

        for name in sorted(exported):
            obj: Any = getattr(api, name, None)
            kind = type(obj).__name__

            if callable(obj):
                try:
                    sig = str(inspect.signature(obj))
                except (TypeError, ValueError):
                    sig = ""
            else:
                sig = ""

            rows.append(f"{name}:{kind}:{sig}")

        payload = "|".join(rows)

    except Exception:
        payload = f"bootstrap:{PACKAGE_VERSION}:{API_VERSION}"

    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# -----------------------------------------------------
# LEGACY TESTED FUNCTION
# Must remain 64-char sha256 string
# -----------------------------------------------------
def compute_api_fingerprint() -> str:
    try:
        import arvis.api as api

        exported = sorted(getattr(api, "__all__", []))
        if not exported:
            raise RuntimeError

        payload = "|".join(exported)

    except Exception:
        payload = f"bootstrap:{PACKAGE_VERSION}:{API_VERSION}"

    return hashlib.sha256(payload.encode()).hexdigest()


# -----------------------------------------------------
# Constants
# -----------------------------------------------------
PUBLIC_API_FINGERPRINT = compute_public_api_fingerprint()

# Existing codebase compatibility
API_FINGERPRINT = compute_api_fingerprint()
