# tests/contracts/test_beta_contract_manifest.py

"""Contract test: the beta surface matches its pinned manifest.

The golden file freezes signatures and schemas, not just names: a
parameter added or removed, a default changed, a dataclass field
retyped, an enum member touched, a property annotation moved, all fail
here. That is the point (audit a13, BETA-02): a modification of the
public contract must break CI until it is made deliberate.

To change the contract deliberately: run
``python scripts/regenerate_beta_manifest.py``, review the golden diff,
record the change in the changelog, and bump ``HOST_API_VERSION`` if a
host_api module moved.
"""

import json
import pathlib

from tests.contracts.beta_manifest import generate_manifest

_GOLDEN = pathlib.Path(__file__).with_name("beta_contract_manifest.json")


def test_beta_contract_matches_the_pinned_manifest() -> None:
    pinned = json.loads(_GOLDEN.read_text(encoding="utf-8"))
    current = generate_manifest()
    assert current == pinned, (
        "The beta contract surface diverged from its pinned manifest. "
        "If the change is deliberate, run "
        "scripts/regenerate_beta_manifest.py, review the golden diff, "
        "record it in the changelog, and bump HOST_API_VERSION if a "
        "host_api module moved."
    )
