# tests/contracts/test_gate_lock_hashes.py
"""The gate lock stays hash-pinned.

Campaign HARDEN (LOT S, audit P1-12, 2026-09-02). The gate
environment installed from a lock with version pins but no hashes:
an index compromise or a substituted artifact under a pinned version
installed silently. The lock now carries sha256 hashes and every
installer passes --require-hashes; this pin makes a hashless
regeneration (dropping --generate-hashes) fail the gate before it
reaches an installer.
"""

from __future__ import annotations

import re
from pathlib import Path

LOCK = Path(__file__).resolve().parents[2] / "requirements" / "gate.lock"


def _pinned_requirements(text: str) -> list[str]:
    return re.findall(r"^([a-z0-9_.-]+)==", text, re.M)


def test_every_pinned_requirement_carries_hashes() -> None:
    text = LOCK.read_text(encoding="utf-8")
    pins = _pinned_requirements(text)
    assert len(pins) > 20, "the lock lost its pins"
    blocks = re.split(r"^(?=[a-z0-9_.-]+==)", text, flags=re.M)
    unhashed = [
        _pinned_requirements(block)[0]
        for block in blocks
        if _pinned_requirements(block) and "--hash=sha256:" not in block
    ]
    assert not unhashed, (
        f"pinned requirement(s) without sha256 hashes: {unhashed}; "
        "regenerate with --generate-hashes"
    )


def test_the_installers_require_the_hashes() -> None:
    root = LOCK.parents[1]
    for rel in (".github/workflows/CI.yml", ".github/workflows/release.yml"):
        text = (root / rel).read_text(encoding="utf-8")
        for line in text.splitlines():
            if "pip install -r requirements/gate.lock" in line:
                assert "--require-hashes" in line, (
                    f"{rel} installs the gate lock without --require-hashes"
                )
