# ARVIS-POSIX Architecture Invariants

This document lists the **non-negotiable invariants** that every compliant implementation must respect.  
They are grouped by layer and enforced at every cognitive step.

## 1. Mathematical Stability Core

- Cognitive state transitions must satisfy Lyapunov stability conditions.
- Symbolic and numeric drift must remain bounded (adaptive ε calibration, IRG-aware).
- Hybrid risk observers must combine deterministic and probabilistic bounds.
- Change budgets and temporal pressure must be respected (no unbounded exploration).
- Regime classification must include hysteresis to avoid oscillations.
- Stability enforcement must occur at runtime (not post-hoc).
- No decision may bypass the gate fusion layer.

## 2. Cognitive Bundle Invariants

- The bundle must be **immutable** (frozen dataclass or equivalent).
- **No prescriptive fields** allowed (no actions, recommendations, "should", "execute", "next_step").
- Explanations must be purely declarative (no causal language: "because", "therefore", "we decided").
- Timeline entries inside the bundle must not include ACTION_* types.
- Context hints limited to shallow primitives (str, bool, int, float, None — no nesting or profiling).
- No callables or hidden logic inside the bundle.
- MemoryLong must be passive (no mutation methods exposed).
- Invariants must be validated on construction (raise on violation).

## 2.1 Canonical Cognitive State Invariants

- `CognitiveState` must be deterministic and serializable.
- Exported state values must respect bounded, normalized contracts.
- Canonical state must be suitable for IR export without hidden runtime mutation.
- Contract validation must happen before externalization whenever applicable.

## 3. Cognitive Timeline Invariants

- Append-only journal — no mutation of past entries.
- Entries classified as STATE (introspection, uncertainty, governance) or EVENT (observed facts).
- Signal types are **closed registry** (finite, explicit, versioned).
- Supersession is deterministic and read-only (older → newer via version).
- Canonical mapping enforced (every signal type/version → fixed category/code/state).
- All entries must be traceable to originating bundle or post-cognitive source.

## 4. Reflexive Snapshot & Self-Model Invariants

- ReflexiveSnapshot must be frozen and filtered (public views only).
- Self-description must combine snapshot + attestation (rendered payload).
- No self-modification or hidden inference allowed.
- Capabilities and principles are declarative and attested.
- Timeline exposure explanation must be built-in and declarative.

## 5. Conversation Orchestration Invariants (partial v0.1)

- Collapse guard must detect and prevent divergence.
- Attractor model must maintain coherence.
- Regime switching must be hysteresis-protected.
- Stability controller must enforce coherence bounds.

**Violation of any invariant results in rejection or non-compliance.**