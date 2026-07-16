# arvis/api/audit.py

from __future__ import annotations

from enum import StrEnum


class AuditCommitmentPolicy(StrEnum):
    """How a missing audit commitment is handled (F-015).

    The audit commitment (global_commitment binding the canonical IR
    hash to the timeline commitment) is the auditability guarantee of
    a run. Its absence must never be silent:

    - REQUIRED: absence is a refusal; building the result view raises
      ArvisSecurityError carrying the reason code. Intended for
      profiles where runs have effects: an unauditable run must not
      pass.
    - DEGRADED (default): the view is produced, but the absence is
      recorded as a visible degradation (commitment_degraded=True)
      together with the reason code.
    - OPTIONAL: absence is tolerated; the reason code is still
      recorded for observability.
    """

    REQUIRED = "required"
    DEGRADED = "degraded"
    OPTIONAL = "optional"
