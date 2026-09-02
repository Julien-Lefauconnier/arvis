# tests/api/test_api_fingerprint.py
"""The emitted API fingerprint measures the real public surface.

Campaign INTEGRITY (LOT I1 / DM-I1, audit P0-4, 2026-09-02).
``API_FINGERPRINT`` was computed eagerly at module import time, while
``arvis/__init__`` was still executing: ``arvis.__all__`` was not yet
bound, the fallback branch fired every time, and the value emitted in
EVERY public result (``to_dict()["fingerprint"]``, documented by the
shipped schema as "Fingerprint of the public root API surface") was
the constant ``sha256("bootstrap:<version>:<api>")``. The only
existing test asserted its length.
"""

from __future__ import annotations

import hashlib

import arvis
from arvis.api import version as version_module
from arvis.api.version import api_fingerprint


def _surface_digest() -> str:
    payload = "|".join(sorted(arvis.__all__))
    return hashlib.sha256(payload.encode()).hexdigest()


def _bootstrap_digest() -> str:
    payload = f"bootstrap:{version_module.PACKAGE_VERSION}:{version_module.API_VERSION}"
    return hashlib.sha256(payload.encode()).hexdigest()


def test_fingerprint_is_the_hash_of_the_sorted_public_surface() -> None:
    """RED on the pre-campaign tree: the value was the bootstrap
    fallback, whatever the surface contained."""
    assert api_fingerprint() == _surface_digest()


def test_fingerprint_is_never_the_bootstrap_fallback_once_imported() -> None:
    assert api_fingerprint() != _bootstrap_digest()


def test_legacy_constant_name_matches_the_lazy_value() -> None:
    """``API_FINGERPRINT`` stays importable (module ``__getattr__``)
    and equals the lazily computed value."""
    assert version_module.API_FINGERPRINT == api_fingerprint()


def test_emitted_result_carries_the_surface_fingerprint() -> None:
    from arvis.api.engine import ArvisEngine

    view = ArvisEngine().run("u1", {"text": "fingerprint probe"})
    payload = view.to_dict()

    assert payload["fingerprint"] == _surface_digest()
    assert len(payload["fingerprint"]) == 64


def test_fingerprint_is_stable_across_calls() -> None:
    assert api_fingerprint() == api_fingerprint()
