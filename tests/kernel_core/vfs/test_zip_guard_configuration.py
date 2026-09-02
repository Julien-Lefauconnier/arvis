# tests/kernel_core/vfs/test_zip_guard_configuration.py
"""The ZIP limits are named, lazy, validated ambient configuration.

Campaign HARDEN (DM-H6, audit P1-14, 2026-09-02). The guard read four
UNPREFIXED environment variables (ZIP_MAX_*) in its class body: they
were resolved once at ``import arvis`` time (a later change of the
environment was silently ignored), a malformed value crashed the
import of the whole package with a bare ValueError, and the names
collided with any host's own ZIP_* variables. The limits are now
resolved at guard construction: ``ARVIS_ZIP_MAX_*`` first, the legacy
unprefixed names as a deprecated beta fallback, a malformed value
raising a typed configuration error naming the variable, and the
effective limits exposed for the governance fingerprint.
"""

from __future__ import annotations

import pytest

from arvis.kernel_core.vfs.zip.guard import (
    ZipConfigurationError,
    ZipGuard,
    effective_zip_limits,
)


def test_limits_resolve_at_construction_not_import(monkeypatch) -> None:
    monkeypatch.setenv("ARVIS_ZIP_MAX_FILE_COUNT", "7")
    guard = ZipGuard()
    assert guard.MAX_FILE_COUNT == 7
    monkeypatch.setenv("ARVIS_ZIP_MAX_FILE_COUNT", "9")
    assert ZipGuard().MAX_FILE_COUNT == 9, (
        "the limit was frozen at import time: it must be read lazily at "
        "guard construction (DM-H6)"
    )


def test_the_prefixed_name_wins_over_the_legacy_fallback(monkeypatch) -> None:
    monkeypatch.setenv("ZIP_MAX_FILE_COUNT", "11")
    assert ZipGuard().MAX_FILE_COUNT == 11  # legacy still honored (beta)
    monkeypatch.setenv("ARVIS_ZIP_MAX_FILE_COUNT", "13")
    assert ZipGuard().MAX_FILE_COUNT == 13  # prefixed wins


def test_a_malformed_value_is_a_typed_error_naming_the_variable(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ARVIS_ZIP_MAX_FILE_COUNT", "abc")
    with pytest.raises(ZipConfigurationError) as excinfo:
        ZipGuard()
    assert "ARVIS_ZIP_MAX_FILE_COUNT" in str(excinfo.value)


def test_a_non_positive_limit_is_refused(monkeypatch) -> None:
    monkeypatch.setenv("ARVIS_ZIP_MAX_TOTAL_SIZE", "0")
    with pytest.raises(ZipConfigurationError):
        ZipGuard()


def test_importing_arvis_never_crashes_on_a_malformed_limit(monkeypatch) -> None:
    """The import-time crash was the audit's probe:
    ZIP_MAX_FILE_COUNT=abc python -c 'import arvis' raised ValueError.
    Resolution is lazy now, so importing the module under a malformed
    environment succeeds; only constructing a guard fails."""
    monkeypatch.setenv("ZIP_MAX_FILE_COUNT", "abc")
    import importlib

    import arvis.kernel_core.vfs.zip.guard as guard_module

    importlib.reload(guard_module)
    with pytest.raises(guard_module.ZipConfigurationError):
        guard_module.ZipGuard()
    monkeypatch.delenv("ZIP_MAX_FILE_COUNT")
    importlib.reload(guard_module)


def test_call_site_injection_still_overrides_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("ARVIS_ZIP_MAX_FILE_COUNT", "7")
    guard = ZipGuard(max_file_count=3)
    assert guard.MAX_FILE_COUNT == 3


def test_effective_limits_are_exposed_for_the_fingerprint(monkeypatch) -> None:
    monkeypatch.setenv("ARVIS_ZIP_MAX_FILE_COUNT", "17")
    limits = effective_zip_limits()
    assert limits["max_file_count"] == 17
    assert set(limits) == {
        "max_total_uncompressed_size",
        "max_file_count",
        "max_file_size",
        "max_compression_ratio",
    }
