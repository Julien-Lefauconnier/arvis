# arvis/reflexive/attestation/reflexive_attestation.py

from __future__ import annotations

import hashlib
import hmac
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from arvis.reflexive.core.reflexive_mode import ReflexiveMode

# Version of the canonicalization rule below. A consumer reading
# canon_version from an attestation knows exactly which transformation
# reproduces the fingerprint (audit a15, A15-BETA-02). Version 2.0
# (audit a16, blocker 2): mode and canon_version enter the canonical
# source, so neither can be rewritten, even consistently across the
# payload and the attestation block, without changing the fingerprint.
ATTESTATION_CANON_VERSION = "2.0"


@dataclass(frozen=True)
class ReflexiveAttestation:
    """Reflexive surface attestation (canonicalization 2.0).

    The fingerprint is computed from the rendered payload after a
    documented, versioned canonicalization:

    - the ``attestation`` key is removed: the attestation is excluded
      from its own fingerprint, so the final public payload verifies
      directly (A15-BETA-02);
    - the volatile ``generated_at`` and the derived ``mode``,
      ``exposed_views`` and ``timeline_views`` keys are removed from
      the payload body;
    - ``timeline_views`` is re-attested filtered to ``exposed_views``
      only, and ``exposed_views`` is attested sorted;
    - ``mode`` and ``canon_version`` are attested members of the
      canonical source (canonicalization 2.0): they cannot be
      rewritten without changing the fingerprint;
    - the source is JSON-serialized with sorted keys and compact
      separators, then hashed with SHA-256.

    :meth:`verify` compares the ENTIRE embedded attestation block to
    its recomputed form (exact keys, exact values, constant-time
    fingerprint comparison): no field of the block, constants and
    flags included, can be modified without failing verification.
    The fingerprint proves structural integrity only, never
    authenticity: it is an unsigned SHA-256, so an actor able to
    rewrite the whole payload can also rewrite its checksum; proving
    origin requires an external anchor held by the host.

    ``deterministic`` means the fingerprint is a pure function of that
    canonical source: no salt, no randomness. Identity across separate
    runs is NOT claimed: the attested state legitimately carries
    decision timestamps. ``immutability`` is true of this object: every
    field is immutable (the view names are a tuple).
    """

    type: str
    scope: str
    authority: str
    immutability: bool
    deterministic: bool
    mode: ReflexiveMode
    exposed_views: tuple[str, ...]
    fingerprint: str
    canon_version: str = ATTESTATION_CANON_VERSION

    @classmethod
    def from_rendered_payload(
        cls,
        rendered_payload: dict[str, Any],
    ) -> ReflexiveAttestation:
        if not isinstance(rendered_payload, dict):
            raise TypeError("rendered_payload must be a dict")

        payload = deepcopy(rendered_payload)

        mode_value = payload.get("mode")
        mode = ReflexiveMode(mode_value)

        if "exposed_views" not in payload:
            raise ValueError("rendered_payload must declare exposed_views")

        exposed_views_raw = payload.get("exposed_views")
        if not isinstance(exposed_views_raw, list):
            raise TypeError("exposed_views must be a list")

        exposed_views = sorted(exposed_views_raw)

        # timeline_views may contain more than exposed views:
        # do not attest hidden / extra views.
        timeline_views_all = payload.get("timeline_views", {})
        if not isinstance(timeline_views_all, dict):
            raise TypeError("timeline_views must be a dict")

        timeline_views = {
            k: v for k, v in timeline_views_all.items() if k in exposed_views
        }

        # The attestation is excluded from its own fingerprint: the
        # canonical source of a final payload and of the pre-attestation
        # rendering are identical (A15-BETA-02).
        payload.pop("attestation", None)
        payload.pop("generated_at", None)
        payload.pop("mode", None)
        payload.pop("exposed_views", None)
        payload.pop("timeline_views", None)

        fingerprint_source = {
            "timeline_views": timeline_views,
            "payload": payload,
            "exposed_views": exposed_views,
            # Canonicalization 2.0: attested members.
            "mode": mode.value,
            "canon_version": ATTESTATION_CANON_VERSION,
        }

        fingerprint = cls._compute_fingerprint(fingerprint_source)

        return cls(
            type="reflexive_snapshot",
            scope="reflexive",
            authority="system",
            immutability=True,
            deterministic=True,
            mode=mode,
            exposed_views=tuple(exposed_views),
            fingerprint=fingerprint,
        )

    @classmethod
    def verify(cls, rendered_payload: object) -> bool:
        """Verify a final public payload against its embedded attestation.

        Recomputes the full attestation from the payload as exposed,
        with no implicit transformation, and compares the ENTIRE
        embedded block to the recomputed one: exact key set, exact
        values for every metadata field (type, scope, authority,
        flags, mode, exposed_views, canon_version), and constant-time
        comparison for the fingerprint. An unknown canon_version is
        refused before any algorithm is applied. Fail-closed for any
        malformed ORDINARY JSON tree (the expected input, as produced
        by json.loads or result.reflexive): every such invalid shape
        returns False. This is a boundary verifier, so unexpected
        exceptions from hostile container subclasses are also absorbed
        (audit a16 blocker 2 and 7.4; audit a17, 13.3).
        """
        try:
            if not isinstance(rendered_payload, dict):
                return False
            embedded = rendered_payload.get("attestation")
            if not isinstance(embedded, dict):
                return False
            if embedded.get("canon_version") != ATTESTATION_CANON_VERSION:
                return False
            recomputed = cls.from_rendered_payload(rendered_payload)
            expected = recomputed.to_dict()
            if set(embedded.keys()) != set(expected.keys()):
                return False
            for key, value in expected.items():
                if key == "fingerprint":
                    continue
                if embedded[key] != value:
                    return False
            published = embedded["fingerprint"]
            if not isinstance(published, str):
                return False
            return hmac.compare_digest(expected["fingerprint"], published)
        except Exception:  # arvis-broad: boundary verifier, fail-closed
            return False

    @staticmethod
    def _compute_fingerprint(source: dict[str, Any]) -> str:
        serialized = json.dumps(
            source,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "scope": self.scope,
            "authority": self.authority,
            "immutability": self.immutability,
            "deterministic": self.deterministic,
            "mode": self.mode.value,
            "exposed_views": list(self.exposed_views),
            "fingerprint": self.fingerprint,
            "canon_version": self.canon_version,
        }
