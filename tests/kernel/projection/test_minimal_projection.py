# tests/kernel/projection/test_minimal_projection.py
"""Minimal projection for bare informational inputs.

A plain text prompt has no structured signals to project. Instead of
hard-blocking on an empty projection, ARVIS attaches a minimal certificate so
the turn is governed by the gate (not surprisingly rejected).
"""

from arvis.api.os import CognitiveOS
from arvis.kernel.projection.certificate import (
    ProjectionCertificationLevel,
    minimal_projection_certificate,
)


def test_minimal_certificate_is_valid_but_flagged():
    cert = minimal_projection_certificate()
    assert cert.domain_valid is True
    assert cert.certification_level is ProjectionCertificationLevel.MINIMAL
    # Honest about not being a full cognitive projection.
    assert cert.checks_detail["minimal_projection"] is True
    assert cert.checks_detail["full_cognitive_projection"] is False


def test_bare_text_input_is_governed_not_hard_blocked():
    data = CognitiveOS().run(user_id="u", cognitive_input="hello").quickstart_payload()
    # Governed (minimal projection), not a surprising projection_invalid block.
    assert data["status"] in ("REQUIRES_CONFIRMATION", "ALLOWED")
