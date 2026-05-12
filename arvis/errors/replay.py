# arvis/errors/replay.py

from __future__ import annotations

from arvis.errors.base import ArvisErrorSeverity, ArvisReplayError


class ReplayVerificationError(ArvisReplayError):
    default_code = "REPLAY_VERIFICATION_FAILED"
    severity = ArvisErrorSeverity.ERROR
    replay_safe = True


class ReplayGlobalCommitmentMissing(ReplayVerificationError):
    default_code = "REPLAY_GLOBAL_COMMITMENT_MISSING"


class ReplayGlobalCommitmentMismatch(ReplayVerificationError):
    default_code = "REPLAY_GLOBAL_COMMITMENT_MISMATCH"


class ReplayCognitiveStateMissing(ReplayVerificationError):
    default_code = "REPLAY_COGNITIVE_STATE_MISSING"
