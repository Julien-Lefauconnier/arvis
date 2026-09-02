# tests/contracts/test_extra_read_ratchet.py
"""Ratchet: internal reads of the ``ctx.extra`` channel are frozen.

Campaign OBS. The doctrine (documented on ``CognitivePipelineContext``)
is that ``extra`` serves exactly two roles: the HOST BOUNDARY CHANNEL
(documented keys a host passes in or reads back) and the write-only
OBSERVABILITY EXPORT of the run's journal. Arvis code reads its own
signals from typed storage (``ctx.journal``, the scientific and
execution sub-contexts), never back from the extra dict, because an
extra read is both a hidden control-flow bus and a potential injection
surface.

This test statically scans ``arvis/`` for every read of an ``.extra``
mapping, resolving local aliases (``extra = getattr(ctx, "extra",
None)``) and classifying subscripts, ``get``/``setdefault``/``pop``
calls, membership tests, iteration and wholesale reads. Every
discovered ``(file, key)`` pair must be in the frozen allowlist below,
and every allowlist entry must still be discovered, in the same
two-direction style as the import-closure ratchet.

To REMOVE an entry: migrate the read to typed storage, then delete the
pair here. To ADD an entry: don't. A new internal extra read needs a
documented boundary justification in one of the categories below, and
those categories are closed on purpose.
"""

from __future__ import annotations

import ast
from pathlib import Path

ARVIS_ROOT = Path(__file__).resolve().parents[2] / "arvis"

# ---------------------------------------------------------------------------
# The frozen allowlist: (file, key) pairs, both directions enforced.
#
# Categories:
#   [host-input]  extra IS the canonical location: the key is written by
#                 the host (or by compliance/test injection channels the
#                 host owns) and read once at its boundary.
#   [accumulator] single-writer export journal the site both creates
#                 and appends to (setdefault-append); nothing branches
#                 on the content.
#   [accessor]    the journal accessors' own duck fallback, and the
#                 guarded fallbacks kept for tolerance contracts on
#                 partial contexts without a journal.
#   [boundary]    a layer that by design sees only a mapping: kernel_core
#                 syscalls (PipelineContextLike), the math-layer gate
#                 policy, the IR record (serialized snapshot, not the
#                 live bus), the error-capture infrastructure, and the
#                 gate observer, which composes the host-facing
#                 observation from the exports.
#   [latch]       the kappa-margin one-shot: the journal is the storage,
#                 but the export pop is still honored on its own so a
#                 seeded forcing flag keeps forcing (F-001).
# ---------------------------------------------------------------------------

ALLOWED_EXTRA_READS: frozenset[tuple[str, str]] = frozenset(
    {
        # ---- [host-input] ----
        ("arvis/api/os.py", "retry_tool"),
        ("arvis/api/os.py", "tool_retry_count"),
        ("arvis/adapters/ir/cognitive_ir_builder.py", "tool_results"),
        ("arvis/cognition/state/cognitive_state_builder.py", "tool_results"),
        ("arvis/kernel/projection/pi_impl.py", "llm_observation"),
        ("arvis/kernel/projection/pi_impl.py", "llm_evaluation"),
        (
            "arvis/kernel/pipeline/services/pipeline_llm_service.py",
            "_allow_mock_runtime",
        ),
        ("arvis/kernel/pipeline/stages/action_stage.py", "retry_tool"),
        ("arvis/kernel/pipeline/stages/bundle_stage.py", "retrieval_snapshot"),
        ("arvis/kernel/pipeline/stages/confirmation_stage.py", "conflict_pressure"),
        ("arvis/kernel/pipeline/stages/conflict_stage.py", "conflict_pressure"),
        ("arvis/kernel/pipeline/stages/core_stage.py", "preserve_injected_lyapunov"),
        ("arvis/kernel/pipeline/stages/core_stage.py", "scientific_state"),
        (
            "arvis/kernel/pipeline/stages/gate/composite.py",
            "preserve_injected_lyapunov",
        ),
        ("arvis/kernel/pipeline/stages/gate/composite.py", "delta_w"),
        ("arvis/kernel/pipeline/stages/gate/composite.py", "stable"),
        ("arvis/kernel/pipeline/stages/gate/context.py", "preserve_injected_lyapunov"),
        ("arvis/kernel/pipeline/stages/gate/context.py", "delta_w"),
        ("arvis/kernel/pipeline/stages/gate/context.py", "stable"),
        ("arvis/kernel/pipeline/stages/tool_feedback_stage.py", "tool_results"),
        ("arvis/tools/retry_policy.py", "tool_retry_count"),
        # ---- [accumulator] ----
        ("arvis/api/runtime/cognitive_runtime.py", "errors"),
        ("arvis/cognition/control/cognitive_control_engine.py", "degraded_components"),
        (
            "arvis/kernel/pipeline/services/pipeline_llm_service.py",
            "llm_structured_outputs",
        ),
        ("arvis/kernel/pipeline/services/pipeline_llm_service.py", "llm_retry_events"),
        (
            "arvis/kernel/pipeline/services/pipeline_llm_service.py",
            "llm_validation_errors",
        ),
        ("arvis/kernel/pipeline/stages/confirmation_stage.py", "debug_events"),
        ("arvis/kernel/pipeline/stages/intent_stage.py", "debug_events"),
        ("arvis/kernel/pipeline/stages/intent_stage.py", "llm"),
        ("arvis/kernel/pipeline/stages/gate/stability.py", "warnings"),
        # ---- [accessor] ----
        ("arvis/kernel/pipeline/context/journal_context.py", "fusion_reasons"),
        (
            "arvis/kernel/pipeline/context/journal_context.py",
            "verdict_transition_trace",
        ),
        ("arvis/kernel/pipeline/context/journal_context.py", "verdict_provenance"),
        ("arvis/kernel/pipeline/stages/confirmation_stage.py", "structural_risk"),
        ("arvis/kernel/pipeline/stages/gate/decision_stack.py", "fusion_trace"),
        ("arvis/kernel/pipeline/stages/gate/input_risk_gate.py", "fusion_reasons"),
        ("arvis/kernel/pipeline/stages/gate/input_risk_gate.py", "kappa_hard_block"),
        ("arvis/kernel/pipeline/stages/projection_stage.py", "pi_structured_available"),
        ("arvis/tools/authorization_service.py", "input_risk"),
        # ---- [boundary] ----
        ("arvis/ir/validation/cognitive_ir_validator.py", "confirmation_override"),
        ("arvis/kernel/observability/gate_observer.py", "*"),
        ("arvis/kernel/pipeline/services/pipeline_ir_bootstrap_service.py", "*"),
        ("arvis/kernel_core/syscalls/intent_outbox.py", "syscall_intents"),
        ("arvis/kernel_core/syscalls/syscall_handler.py", "audit_incomplete_syscalls"),
        ("arvis/kernel_core/syscalls/syscall_handler.py", "syscall_results"),
        ("arvis/math/gate/gate_policy.py", "fusion_reasons"),
        ("arvis/math/gate/gate_policy.py", "recovery_detected"),
        # ---- [latch] ----
        (
            "arvis/kernel/pipeline/stages/gate/adaptive.py",
            "_kappa_margin_forced_confirmation",
        ),
    }
)


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


def _is_extra_getattr(node: ast.AST) -> bool:
    """``getattr(x, "extra", ...)`` calls."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == "extra"
    )


class _FunctionScanner(ast.NodeVisitor):
    """Scans one function body, tracking local extra-dict aliases."""

    READ_METHODS = {"get", "setdefault", "pop"}
    WHOLESALE_METHODS = {"keys", "items", "values", "copy"}
    WRITE_METHODS = {"update", "clear"}

    def __init__(self, relpath: str, reads: set[tuple[str, str]]) -> None:
        self.relpath = relpath
        self.reads = reads
        self.aliases: set[str] = set()
        self._parents: dict[int, ast.AST] = {}

    # -- helpers ---------------------------------------------------------

    def _is_extra_expr(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Attribute) and node.attr == "extra":
            return True
        if _is_extra_getattr(node):
            return True
        return isinstance(node, ast.Name) and node.id in self.aliases

    def _key_of(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return "*"

    def _record(self, key: str) -> None:
        self.reads.add((self.relpath, key))

    # -- alias tracking --------------------------------------------------

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._is_extra_expr(node.value):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.aliases.add(target.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None and self._is_extra_expr(node.value):
            if isinstance(node.target, ast.Name):
                self.aliases.add(node.target.id)
        self.generic_visit(node)

    # -- read forms ------------------------------------------------------

    def visit_Subscript(self, node: ast.Subscript) -> None:
        if self._is_extra_expr(node.value) and isinstance(node.ctx, ast.Load):
            self._record(self._key_of(node.slice))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and self._is_extra_expr(func.value):
            if func.attr in self.READ_METHODS:
                self._record(self._key_of(node.args[0]) if node.args else "*")
            elif func.attr in self.WHOLESALE_METHODS:
                self._record("*")
            elif func.attr not in self.WRITE_METHODS:
                self._record("*")
        elif isinstance(func, ast.Name) and func.id == "isinstance":
            # A type guard on the mapping is not a read; do not descend
            # into the guarded expression itself.
            for arg in node.args[1:]:
                self.visit(arg)
            return
        elif not _is_extra_getattr(node):
            # Any other call receiving the mapping wholesale reads it:
            # dict(extra), len(extra), sorted(extra), json.dumps(extra).
            for arg in node.args:
                if self._is_extra_expr(arg):
                    self._record("*")
            for kw in node.keywords:
                if kw.value is not None and self._is_extra_expr(kw.value):
                    self._record("*")
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> None:
        left = node.left
        for op, comp in zip(node.ops, node.comparators, strict=True):
            if isinstance(op, (ast.In, ast.NotIn)) and self._is_extra_expr(comp):
                self._record(self._key_of(left))
            left = comp
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        if self._is_extra_expr(node.iter):
            self._record("*")
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        # ``ir_context.extra or {}``: the mapping's truthiness (and, on
        # truthy, its content) is consumed wholesale.
        for value in node.values:
            if self._is_extra_expr(value):
                self._record("*")
        self.generic_visit(node)


class _ModuleScanner(ast.NodeVisitor):
    """Runs a fresh _FunctionScanner per function scope."""

    def __init__(self, relpath: str) -> None:
        self.relpath = relpath
        self.reads: set[tuple[str, str]] = set()

    def _scan_function(self, node: ast.AST) -> None:
        scanner = _FunctionScanner(self.relpath, self.reads)
        body = getattr(node, "body", [])
        # Two passes so an alias assigned later in the body still marks
        # earlier reads (conservative; ordering games don't hide reads).
        for _ in range(2):
            for stmt in body:
                scanner.visit(stmt)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._scan_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._scan_function(node)
        self.generic_visit(node)


def scan_extra_reads() -> set[tuple[str, str]]:
    reads: set[tuple[str, str]] = set()
    for py_file in sorted(ARVIS_ROOT.rglob("*.py")):
        relpath = str(py_file.relative_to(ARVIS_ROOT.parent))
        tree = ast.parse(py_file.read_text(encoding="utf-8"))
        module_scanner = _ModuleScanner(relpath)
        module_scanner.visit(tree)
        # Module-level statements (outside any function) get one pass too.
        top = _FunctionScanner(relpath, module_scanner.reads)
        for stmt in tree.body:
            if not isinstance(
                stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                top.visit(stmt)
        reads |= module_scanner.reads
    return reads


def _collapse_wildcards(reads: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """A file allowlisted with "*" covers all its keyed reads."""
    wildcard_files = {f for f, k in ALLOWED_EXTRA_READS if k == "*"}
    return {("" + f, "*") if f in wildcard_files else (f, k) for f, k in reads}


# ---------------------------------------------------------------------------
# The two ratchet directions
# ---------------------------------------------------------------------------


def test_no_new_internal_extra_reads() -> None:
    """Direction 1: every internal extra read is allowlisted."""
    discovered = _collapse_wildcards(scan_extra_reads())
    unexpected = discovered - ALLOWED_EXTRA_READS
    assert not unexpected, (
        "New internal read(s) of ctx.extra detected:\n  "
        + "\n  ".join(f"{f}: {k!r}" for f, k in sorted(unexpected))
        + "\nThe extra dict is a host boundary channel and a write-only "
        "export journal; arvis reads its own signals from typed storage "
        "(ctx.journal, the scientific/execution sub-contexts). Migrate "
        "the read instead of extending ALLOWED_EXTRA_READS."
    )


def test_no_stale_allowlist_entries() -> None:
    """Direction 2: every allowlist entry still corresponds to a read.

    When a migration removes a read, its entry must be deleted here so
    the ratchet keeps tightening and the list stays an honest map of
    the remaining boundary.
    """
    discovered = _collapse_wildcards(scan_extra_reads())
    stale = ALLOWED_EXTRA_READS - discovered
    assert not stale, (
        "Stale ALLOWED_EXTRA_READS entries (no longer read):\n  "
        + "\n  ".join(f"{f}: {k!r}" for f, k in sorted(stale))
        + "\nDelete them so the ratchet tightens."
    )
