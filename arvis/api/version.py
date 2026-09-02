# arvis/api/version.py

from __future__ import annotations

import hashlib
from importlib.metadata import PackageNotFoundError, version
from typing import Final

# -----------------------------------------------------
# Versioning axes (0.1.0-beta)
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
    PACKAGE_VERSION = "0.1.0b6"


# -----------------------------------------------------
# Public API contract version
# -----------------------------------------------------
# The 0.1 public API is stable within the beta series under VERSIONING.md.
# This intentionally reads "0.1" (not "1.0.0") so the emitted contract
# does not over-promise cross-minor or 1.0 stability.
API_VERSION: Final[str] = "0.1"


# -----------------------------------------------------
# ARVIS standard / specification version
# -----------------------------------------------------
# The mathematical and IR specifications are draft-level for 0.1.
STANDARD_VERSION: Final[str] = "draft-v1"


# -----------------------------------------------------
# API surface fingerprint (lazy, cached)
# -----------------------------------------------------
# Campaign INTEGRITY (DM-I1, audit P0-4): this used to be an EAGER
# module constant computed while ``arvis/__init__`` was still
# executing. ``arvis.__all__`` was not bound yet, so the fallback
# branch fired on every import and the value emitted in every public
# result was the bootstrap constant, never the surface hash the
# shipped schema documents. The fingerprint is now computed on first
# use, after the root package is fully initialized, and cached.
_FINGERPRINT_CACHE: str | None = None


def compute_api_fingerprint() -> str:
    """Fingerprint of the public root API surface (uncached).

    ``sha256("|".join(sorted(arvis.__all__)))``; the bootstrap
    fallback only ever applies when the root package genuinely cannot
    be imported (a partial checkout), never on a normal import.
    """
    try:
        import arvis

        exported = getattr(arvis, "__all__", None)
        if not exported:
            raise RuntimeError
        payload = "|".join(sorted(exported))
    except (ImportError, RuntimeError):
        payload = f"bootstrap:{PACKAGE_VERSION}:{API_VERSION}"
    return hashlib.sha256(payload.encode()).hexdigest()


def api_fingerprint() -> str:
    """Cached fingerprint of the public root API surface."""
    global _FINGERPRINT_CACHE
    if _FINGERPRINT_CACHE is None:
        _FINGERPRINT_CACHE = compute_api_fingerprint()
    return _FINGERPRINT_CACHE


def __getattr__(name: str) -> str:
    # Backward-compatible module attribute: the historical constant
    # name keeps working, now resolving to the lazy value.
    if name == "API_FINGERPRINT":
        return api_fingerprint()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
