# arvis/api/version.py

from __future__ import annotations

import hashlib
import arvis.api as api


API_VERSION = "1.0.0"


def compute_api_fingerprint() -> str:
    exported = sorted(getattr(api, "__all__", []))
    joined = "|".join(exported)
    return hashlib.sha256(joined.encode()).hexdigest()


API_FINGERPRINT = compute_api_fingerprint()