# tests/contracts/test_env_configuration_registry.py
"""Every ambient-environment read is registered and documented.

Campaign HARDEN (DM-H6, audit P1-14, 2026-09-02). The audit found the
ZIP limits read unprefixed in a class body (import-time crash on a
malformed value) and none of the variables documented anywhere. The
registry below IS the contract, mirrored by docs/CONFIGURATION.md: a
new os.getenv / os.environ read in arvis/ outside the registered
(file, variable) sites fails the gate, so configuration cannot grow
back undocumented, unprefixed or import-resolved.
"""

from __future__ import annotations

import ast
from pathlib import Path

ARVIS = Path(__file__).resolve().parents[2] / "arvis"

# The registered ambient reads: file (repo-relative) -> variables it
# may read. Adding an entry here REQUIRES documenting the variable in
# docs/CONFIGURATION.md (checked below) and reading it lazily.
REGISTERED_READS: dict[str, set[str]] = {
    # The guard resolves its four limits through one validated helper
    # with a computed name (ARVIS_<name> then legacy <name>); the
    # concrete variable set is derived from its _LIMIT_DEFAULTS table
    # and checked against the doc below.
    "arvis/kernel_core/vfs/zip/guard.py": {"<dynamic>"},
    "arvis/cognition/gate/reason_code_normalizer.py": {"ARVIS_REASON_STRICT"},
    "arvis/kernel/pipeline/services/pipeline_bootstrap_service.py": {
        "ARVIS_STRICT_STABILITY"
    },
    "arvis/adapters/llm/providers/resolver.py": {
        "ARVIS_LLM_PROVIDER",
        "ARVIS_LLM_MODEL",
    },
}

CONFIGURATION_DOC = ARVIS.parent / "docs" / "CONFIGURATION.md"


def _env_reads(path: Path) -> set[str]:
    """Variable names read via os.getenv/os.environ in one file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        # os.getenv("X", ...) / os.environ.get("X", ...)
        if isinstance(node, ast.Call):
            func = node.func
            is_getenv = (
                isinstance(func, ast.Attribute)
                and func.attr in {"getenv", "get"}
                and (
                    (isinstance(func.value, ast.Name) and func.value.id == "os")
                    or (
                        isinstance(func.value, ast.Attribute)
                        and func.value.attr == "environ"
                    )
                )
            )
            if is_getenv and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    names.add(first.value)
                else:
                    names.add("<dynamic>")
        # os.environ["X"]
        if isinstance(node, ast.Subscript):
            value = node.value
            if isinstance(value, ast.Attribute) and value.attr == "environ":
                names.add("<subscript>")
    return names


def _all_reads() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for path in sorted(ARVIS.rglob("*.py")):
        rel = "arvis/" + path.relative_to(ARVIS).as_posix()
        names = _env_reads(path)
        if names:
            found[rel] = names
    return found


def test_every_env_read_is_registered() -> None:
    unregistered = {
        rel: sorted(names - REGISTERED_READS.get(rel, set()))
        for rel, names in _all_reads().items()
        if names - REGISTERED_READS.get(rel, set())
    }
    assert not unregistered, (
        f"unregistered ambient-environment read(s): {unregistered}. "
        "Register the (file, variable) here AND document the variable "
        "in docs/CONFIGURATION.md (DM-H6)."
    )


def test_no_registered_site_went_stale() -> None:
    """A registered site that no longer reads its variable is removed
    from the registry (and from the doc) rather than left over."""
    reads = _all_reads()
    stale = {
        rel: sorted(expected - reads.get(rel, set()))
        for rel, expected in REGISTERED_READS.items()
        if expected - reads.get(rel, set())
    }
    assert not stale, f"registry entries no longer read in code: {stale}"


def _zip_guard_variables() -> set[str]:
    from arvis.kernel_core.vfs.zip.guard import _LIMIT_DEFAULTS

    return {
        prefixed for name in _LIMIT_DEFAULTS for prefixed in (name, f"ARVIS_{name}")
    }


def test_every_registered_variable_is_documented() -> None:
    doc = CONFIGURATION_DOC.read_text(encoding="utf-8")
    variables = {
        variable
        for names in REGISTERED_READS.values()
        for variable in names
        if variable != "<dynamic>"
    }
    variables |= _zip_guard_variables()
    undocumented = sorted(v for v in variables if v not in doc)
    assert not undocumented, (
        f"registered variable(s) missing from docs/CONFIGURATION.md: {undocumented}"
    )
