# tests/contracts/test_control_engine_isolation.py
"""The kernel never imports the host-side control engine.

Campaign SURFACE (DM-S3, audit P1-8, 2026-09-02). The repo carries two
verdict-producing components: the gate decision stack (the governed
verdict, on the pipeline path) and ``CognitiveControlEngine`` (a
host-side control runtime, exported PROVISIONAL through
``host_api.control`` and consumed by hosts, never instantiated by the
pipeline). The decided posture is to keep the second and declare it
for what it is; this ratchet makes the declaration structural: no
module of the kernel decision path may import the host-side engine,
so it cannot silently become a second producer of the governed
verdict. Its only importers inside ``arvis/`` are its own package and
the ``host_api.control`` re-export layer.
"""

from __future__ import annotations

import ast
from pathlib import Path

ARVIS = Path(__file__).resolve().parents[2] / "arvis"

ENGINE_MODULE = "arvis.cognition.control.cognitive_control_engine"

ALLOWED_IMPORTERS = {
    # Its own package (runtime, snapshot, package __init__).
    "arvis/cognition/control",
    # The pinned host re-export layer.
    "arvis/host_api/control.py",
}


def _imports_engine(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.startswith(ENGINE_MODULE) for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith(ENGINE_MODULE):
                return True
    return False


def _is_allowed(rel: str) -> bool:
    return any(
        rel == allowed or rel.startswith(allowed + "/") for allowed in ALLOWED_IMPORTERS
    )


def test_only_the_control_package_and_host_api_import_the_engine() -> None:
    offenders = []
    for path in sorted(ARVIS.rglob("*.py")):
        rel = path.relative_to(ARVIS.parent).as_posix().removeprefix("arvis/")
        rel = f"arvis/{rel}"
        if _imports_engine(path) and not _is_allowed(rel):
            offenders.append(rel)
    assert not offenders, (
        f"{offenders} import the host-side CognitiveControlEngine: the "
        "kernel decision path must never route through it (DM-S3); the "
        "gate decision stack is the only producer of the governed verdict"
    )


def test_the_scan_sees_the_legitimate_importers() -> None:
    """The ratchet is not vacuous: the re-export layer is seen
    importing the engine (a renamed module would blind the scan)."""
    host_control = ARVIS / "host_api" / "control.py"
    assert _imports_engine(host_control)
