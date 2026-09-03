# tests/contracts/test_commitment_composition_pin.py
"""The commitment composition cannot drift without a version bump.

Campaign RELEASE-b7 (2026-09-03). VERSIONS.md states the consumer
rule: a commitment that no longer verifies after an upgrade is
expected behaviour if CANONICALIZATION_VERSION or COMMITMENT_VERSION
changed, and a defect otherwise. Campaign HARDEN widened what
``config_fingerprint`` covers (confirmation registry, effective ZIP
limits, module+qualname identity binding) and what
``policies_fingerprint`` commits to (kappa band table, canonical
switching parameters): the right hardening, but a 0.1.0b6 commitment
stopped recomposing under the same COMMITMENT_VERSION 6, which is
exactly the defect class the b6 release closed for canonical bytes.

This pin makes the drift loud at change time instead of release
time: the two governance fingerprints of a default build are golden.
Updating these literals is legitimate ONLY in a change that also
moves COMMITMENT_VERSION and records the invalidation in the
changelog Security section; with the b6 goldens in place, campaign
HARDEN would have failed this test on the day it widened the
composition.
"""

from __future__ import annotations

import pytest

from arvis import CognitiveOS
from arvis.api.commitment import (
    COMMITMENT_VERSION,
    config_fingerprint,
    policies_fingerprint,
)

# Minted under COMMITMENT_VERSION 7 on the default build (no
# ARVIS_ZIP_*/ZIP_* environment overrides; the fixture below clears
# them so a developer's shell cannot move a governance digest).
GOLDEN_CONFIG_FINGERPRINT = (
    "c3ac36aa416e217f56717d48c170c67c9f28a0a70290f7729212b12e92212bd9"
)
GOLDEN_POLICIES_FINGERPRINT = (
    "f82bf470c5fc15f38d90a045f2b02d1ddc4ba9e4e9f3ef5292b61b958e43bf4d"
)

_ZIP_ENV_NAMES = [
    prefix + name
    for name in (
        "ZIP_MAX_TOTAL_SIZE",
        "ZIP_MAX_FILE_COUNT",
        "ZIP_MAX_FILE_SIZE",
        "ZIP_MAX_COMPRESSION_RATIO",
    )
    for prefix in ("ARVIS_", "")
]


@pytest.fixture()
def _default_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _ZIP_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_commitment_version_is_the_declared_one() -> None:
    assert COMMITMENT_VERSION == 7


def test_config_fingerprint_of_the_default_build_is_pinned(
    _default_environment: None,
) -> None:
    assert config_fingerprint(CognitiveOS().config) == GOLDEN_CONFIG_FINGERPRINT


def test_policies_fingerprint_is_pinned(_default_environment: None) -> None:
    assert policies_fingerprint() == GOLDEN_POLICIES_FINGERPRINT
