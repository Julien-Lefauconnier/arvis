# tests/api/test_replay_authentication.py
"""Replay authentication requires an external anchor (campaign 5, D-6).

The a7 audit (P1-7) showed replay_verified(ir) with no expected
commitment recomposing and accepting arbitrary fingerprints: replaying
an IR and trusting the commitment it carries about itself proves
nothing. Authentication now requires an external commitment the caller
supplies from a durable source OUTSIDE the IR (a signed record, an
append-only journal, a host attestation); the host owns that source's
durability.
"""

from __future__ import annotations

import pytest

from arvis.api import CognitiveOS


def test_forged_commitment_is_rejected():
    # The exact a7 attack: recompose and try to authenticate against an
    # arbitrary fingerprint. It must be refused.
    os = CognitiveOS()
    run = os.run("u1", {"risk": 0.1})
    ir = run.to_ir()
    with pytest.raises(RuntimeError, match="global_commitment mismatch"):
        os.replay_verified(ir, expected_global_commitment="b" * 64)


def test_authentication_requires_an_external_commitment():
    # An empty expected commitment is not an authentication: it is
    # refused with a message pointing to replay_recomposed.
    os = CognitiveOS()
    run = os.run("u1", {"risk": 0.1})
    ir = run.to_ir()
    with pytest.raises(RuntimeError, match="external anchor"):
        os.replay_verified(ir, expected_global_commitment="")


def test_legitimate_external_commitment_authenticates():
    # The caller supplies the commitment recorded from the original run
    # (here read back from the run; a real host reads it from its
    # durable anchor). Recomposition matches it, so the call returns.
    os = CognitiveOS()
    run = os.run("u1", {"risk": 0.1})
    external_anchor = run.global_commitment  # a host reads this from durable storage
    replayed = os.replay_verified(
        run.to_ir(), expected_global_commitment=external_anchor
    )
    assert replayed.global_commitment == external_anchor


def test_recomposition_is_available_without_authentication():
    # A caller with no anchor recomposes explicitly, with no trust claim.
    os = CognitiveOS()
    run = os.run("u1", {"risk": 0.1})
    replayed = os.replay_recomposed(run.to_ir())
    assert replayed is not None
