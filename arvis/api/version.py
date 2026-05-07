# arvis/api/version.py

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, version
from typing import Final

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
API_VERSION: Final[str] = "1.0.0"


# -----------------------------------------------------
# New short fingerprint (optional modern export)
# -----------------------------------------------------
def compute_public_api_fingerprint() -> str:
    try:
        import arvis

        exported = getattr(arvis, "__all__", None)
        if not exported:
            raise RuntimeError
        payload = "|".join(sorted(exported))
    except Exception:
        payload = f"bootstrap:{PACKAGE_VERSION}:{API_VERSION}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


# -----------------------------------------------------
# LEGACY TESTED FUNCTION (64 chars)
# Must remain 64-char sha256 string
# -----------------------------------------------------
def compute_api_fingerprint() -> str:
    try:
        import arvis

        exported = getattr(arvis, "__all__", None)
        if not exported:
            raise RuntimeError
        payload = "|".join(sorted(exported))
    except Exception:
        payload = f"bootstrap:{PACKAGE_VERSION}:{API_VERSION}"
    return hashlib.sha256(payload.encode()).hexdigest()


# -----------------------------------------------------
# Public constants (eager, safe via fallback)
# -----------------------------------------------------
API_FINGERPRINT: Final[str] = compute_api_fingerprint()
PUBLIC_API_FINGERPRINT: Final[str] = compute_public_api_fingerprint()
