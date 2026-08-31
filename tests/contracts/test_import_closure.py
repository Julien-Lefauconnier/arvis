# tests/contracts/test_import_closure.py
"""Ratchet: no module of ``arvis/`` may quietly become unreachable.

Reachability is computed statically (ast-level imports) from three
root sets that together define the supported surface:

- ``arvis`` itself (the public ``__init__``),
- every ``arvis.host_api`` module (the documented host surface),
- every module of the veramem consumed surface
  (``tests/contracts/test_veramem_consumed_surface.py``), since the
  host imports deep paths the public ``__init__`` does not reach.

A module reachable from none of these is dead weight: it still counts
in the coverage denominator, keeps its tests alive, and collides with
living names (audit A2, 2026-08, found 91 such modules; the veramem
surface legitimizes a part of them).

The frozen KNOWN_UNREACHABLE list below is a burn-down, not a licence:

- a module that becomes unreachable and is NOT listed fails the test
  (no new dead code);
- a listed module that becomes reachable, or disappears, also fails
  (the list must shrink with reality, never lag behind it).

Removing an entry is the desired direction; adding one requires the
same justification as adding dead code, because it is one.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.contracts.test_veramem_consumed_surface import CONSUMED_SURFACE

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "arvis"

# Burn-down list frozen 2026-08-31 (campaign "mise au propre", LOT 7).
# Every entry was verified unreachable from the three root sets at that
# date. The largest block is the standalone conversation orchestration
# layer (only continuation/pending_turn are consumed); the math block is
# the predictive/probabilistic layer the default engine does not drive.
KNOWN_UNREACHABLE: frozenset[str] = frozenset(
    {
        "arvis.adapters.kernel.kernel_adapter",
        "arvis.adapters.kernel.mappers",
        "arvis.adapters.kernel.mappers.ir_to_canonical",
        "arvis.adapters.kernel.rules",
        "arvis.adapters.kernel.rules.base_rule",
        "arvis.adapters.kernel.rules.decision_rules",
        "arvis.adapters.kernel.rules.fallback_rules",
        "arvis.adapters.kernel.rules.gate_rules",
        "arvis.adapters.kernel.rules.state_rules",
        "arvis.adapters.kernel.signals.signal_semantics",
        "arvis.adapters.llm.contracts.error_payload",
        "arvis.adapters.llm.contracts.result",
        "arvis.adapters.llm.observability.providers",
        "arvis.adapters.llm.observability.providers.base",
        "arvis.adapters.llm.observability.providers.mock",
        "arvis.adapters.llm.observability.risk_mapper",
        "arvis.api.cognition",
        "arvis.api.math",
        "arvis.api.memory",
        "arvis.api.reasoning",
        "arvis.cognition.confirmation.confirmation_flow",
        "arvis.cognition.conflict.conflict_impact",
        "arvis.cognition.projection.projection_api",
        "arvis.conversation.act_strategy_mapper",
        "arvis.conversation.conversation_adaptive_controller",
        "arvis.conversation.conversation_adaptive_policy",
        "arvis.conversation.conversation_adversarial_detector",
        "arvis.conversation.conversation_attractor_model",
        "arvis.conversation.conversation_cognitive_bridge",
        "arvis.conversation.conversation_coherence_metric",
        "arvis.conversation.conversation_collapse_guard",
        "arvis.conversation.conversation_composite_stability",
        "arvis.conversation.conversation_context",
        "arvis.conversation.conversation_energy_model",
        "arvis.conversation.conversation_entropy_regulator",
        "arvis.conversation.conversation_feedback_signal",
        "arvis.conversation.conversation_future_simulator",
        "arvis.conversation.conversation_global_stability_adapter",
        "arvis.conversation.conversation_lyapunov_adapter",
        "arvis.conversation.conversation_memory_bridge",
        "arvis.conversation.conversation_memory_policy",
        "arvis.conversation.conversation_orchestrator",
        "arvis.conversation.conversation_policy_base",
        "arvis.conversation.conversation_policy_engine",
        "arvis.conversation.conversation_predictive_strategy",
        "arvis.conversation.conversation_predictor",
        "arvis.conversation.conversation_regime_controller",
        "arvis.conversation.conversation_stability_controller",
        "arvis.conversation.conversation_stability_signals",
        "arvis.conversation.conversation_state",
        "arvis.conversation.conversation_strategy_dynamics",
        "arvis.conversation.conversation_trajectory_controller",
        "arvis.conversation.conversation_world_prediction_bridge",
        "arvis.conversation.response_plan",
        "arvis.conversation.response_plan_builder",
        "arvis.conversation.response_realization_mode",
        "arvis.conversation.response_strategy_decision",
        "arvis.conversation.response_strategy_resolver",
        "arvis.conversation.response_strategy_type",
        "arvis.conversation.strategy_stability_controller",
        "arvis.conversation.user_adaptive_profile",
        "arvis.kernel_core.process.snapshot",
        "arvis.kernel_core.vfs.repositories",
        "arvis.kernel_core.vfs.repositories.in_memory",
        "arvis.linguistic.acts.gate_mapping",
        "arvis.linguistic.acts.linguistic_act",
        "arvis.linguistic.generation.frame_builder",
        "arvis.linguistic.generation.prompt_builder",
        "arvis.linguistic.lexicon",
        "arvis.linguistic.lexicon.lexicon_entry",
        "arvis.linguistic.lexicon.lexicon_snapshot",
        "arvis.math.control.beta_adaptive",
        "arvis.math.core.local_dynamics",
        "arvis.math.core.stability_certificate",
        "arvis.math.drift.drift_detector",
        "arvis.math.lyapunov.probabilistic_lyapunov",
        "arvis.math.predictive",
        "arvis.math.predictive.predictive_multi_horizon",
        "arvis.math.predictive.predictive_stability",
        "arvis.math.predictive.trajectory_observer",
        "arvis.math.risk.risk_calibration",
        "arvis.math.stability.global_stability",
        "arvis.math.stability.hybrid_risk_observer",
        "arvis.math.stability.multi_horizon_stability",
        "arvis.math.stability.theorem",
        "arvis.runtime.runtime_snapshot",
        "arvis.runtime.runtime_snapshot_builder",
        "arvis.signals.canonical.canonical_signal_invariants",
        "arvis.signals.signal",
        "arvis.signals.signal_invariants",
        "arvis.telemetry.redaction",
    }
)


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _all_modules() -> dict[str, Path]:
    return {
        _module_name(p): p
        for p in PACKAGE.rglob("*.py")
        if "__pycache__" not in p.parts
    }


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("arvis"):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # relative import: resolve against this module's package
                base = _module_name(path).split(".")
                if path.name != "__init__.py":
                    base = base[:-1]
                base = base[: len(base) - (node.level - 1)]
                prefix = ".".join(base)
                module = f"{prefix}.{node.module}" if node.module else prefix
            else:
                module = node.module or ""
            if module.startswith("arvis"):
                found.add(module)
                for alias in node.names:
                    found.add(f"{module}.{alias.name}")
    return found


def _closure(roots: set[str], modules: dict[str, Path]) -> set[str]:
    reached: set[str] = set()
    stack = [r for r in roots if r in modules]
    while stack:
        name = stack.pop()
        if name in reached:
            continue
        reached.add(name)
        # importing a module executes every ancestor package __init__
        parts = name.split(".")
        for i in range(1, len(parts)):
            ancestor = ".".join(parts[:i])
            if ancestor in modules and ancestor not in reached:
                stack.append(ancestor)
        for imported in _imports_of(modules[name]):
            candidates = [imported]
            # "from pkg.mod import symbol" adds pkg.mod.symbol; keep the
            # module part too when the symbol is not itself a module.
            if imported not in modules and "." in imported:
                candidates.append(imported.rsplit(".", 1)[0])
            for candidate in candidates:
                if candidate in modules and candidate not in reached:
                    stack.append(candidate)
    return reached


def _unreachable_now() -> set[str]:
    modules = _all_modules()
    roots = {"arvis"}
    roots.update(name for name in modules if name.startswith("arvis.host_api"))
    roots.update(CONSUMED_SURFACE.keys())
    reached = _closure(roots, modules)
    return {name for name in modules if name not in reached}


def test_no_new_unreachable_modules() -> None:
    unreachable = _unreachable_now()
    new = unreachable - KNOWN_UNREACHABLE
    assert not new, (
        f"{len(new)} module(s) became unreachable from the supported "
        "surface (public API + host_api + veramem consumed surface). "
        "Either wire them, delete them, or add them to KNOWN_UNREACHABLE "
        "with a justification:\n  " + "\n  ".join(sorted(new))
    )


def test_burn_down_list_matches_reality() -> None:
    unreachable = _unreachable_now()
    stale = KNOWN_UNREACHABLE - unreachable
    assert not stale, (
        "these KNOWN_UNREACHABLE entries are now reachable or deleted; "
        "remove them from the list so it keeps matching reality:\n  "
        + "\n  ".join(sorted(stale))
    )
