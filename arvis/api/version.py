# arvis/api/version.py

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, version
from typing import Final

# -----------------------------------------------------
# Versioning axes (0.1.0-alpha)
# -----------------------------------------------------
# Three distinct axes are tracked, each honestly labeled and mutually
# consistent. They are NOT the same string on purpose:
#
#   PACKAGE_VERSION  -> the distributed artifact (PEP 440), from pyproject.
#   API_VERSION      -> the public Python API contract.          "0.1"
#   STANDARD_VERSION -> the ARVIS decision/IR standard spec.     "draft-v1"
#
# Single source of truth for PACKAGE_VERSION is pyproject.toml; the fallback
# below is used only for uninstalled source checkouts and must mirror it.
# -----------------------------------------------------

# -----------------------------------------------------
# Installed package version
# -----------------------------------------------------
try:
    PACKAGE_VERSION = version("arvis")
except PackageNotFoundError:
    PACKAGE_VERSION = "0.1.0a5"


# -----------------------------------------------------
# Public API contract version
# -----------------------------------------------------
# Alpha: the public API is not yet stable. This intentionally reads "0.1"
# (not "1.0.0") so the emitted contract does not over-promise stability.
API_VERSION: Final[str] = "0.1"


# -----------------------------------------------------
# ARVIS standard / specification version
# -----------------------------------------------------
# The mathematical and IR specifications are draft-level for 0.1.
STANDARD_VERSION: Final[str] = "draft-v1"


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
    except (ImportError, RuntimeError):
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
    except (ImportError, RuntimeError):
        payload = f"bootstrap:{PACKAGE_VERSION}:{API_VERSION}"
    return hashlib.sha256(payload.encode()).hexdigest()


# -----------------------------------------------------
# Public constants (eager, safe via fallback)
# -----------------------------------------------------
API_FINGERPRINT: Final[str] = compute_api_fingerprint()
PUBLIC_API_FINGERPRINT: Final[str] = compute_public_api_fingerprint()
