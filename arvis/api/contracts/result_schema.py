# arvis/api/contracts/result_schema.py

"""Loader and version of the public result serialization contract."""

from __future__ import annotations

import importlib.resources
import json
from typing import Any

RESULT_SCHEMA_VERSION = "1.0"
_SCHEMA_FILENAME = "cognitive_result_v1.schema.json"


def load_result_schema() -> dict[str, Any]:
    """The JSON Schema of CognitiveResultView.to_dict(), as shipped.

    Loaded from the installed package so contract tests and the
    black-box compliance suite validate the exact artifact a consumer
    receives.
    """
    resource = importlib.resources.files("arvis.api.contracts").joinpath(
        _SCHEMA_FILENAME
    )
    return json.loads(resource.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
