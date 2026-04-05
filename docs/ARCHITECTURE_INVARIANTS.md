# ARVIS-POSIX Architecture Invariants

This document lists the **non-negotiable invariants** that every compliant implementation must respect.  
They are grouped by layer and enforced at every cognitive step.

## 0. Runtime & Scheduler Invariants

- At most **one RUNNING process** at any time (single execution invariant).
- A process MUST belong to exactly one scheduler state:
  - READY
  - RUNNING
  - WAITING_CONFIRMATION
  - BLOCKED
  - SUSPENDED
  - COMPLETED
  - ABORTED

- Terminal states are:
  - COMPLETED
  - WAITING_CONFIRMATION
  - ABORTED

  → Terminal processes MUST NOT be re-enqueued.

- Scheduler MUST be deterministic:
  - identical state → identical scheduling decision

- Each scheduler tick MUST:
  - select at most one process
  - execute at most one pipeline step

- Execution MUST be preemptive:
  - processes return to READY if not completed

- A process MUST NOT remain in READY after execution without:
  - being re-enqueued
  - or transitioned to another valid state

- Budget constraints MUST be enforced:
  - no process may execute without available budget

- Errors during execution MUST:
  - transition process to ABORTED
  - be recorded in runtime state

- Runtime MUST NOT alter cognitive semantics:
  - no modification of decision logic
  - no mutation of pipeline outputs

- Runtime MUST preserve execution determinism:
   - scheduling decisions MUST be reproducible
   - process selection MUST be deterministic

---

## 1. Mathematical Stability Core

- Cognitive state transitions must satisfy Lyapunov stability conditions.
- Symbolic and numeric drift must remain bounded (adaptive ε calibration, IRG-aware).
- Hybrid risk observers must combine deterministic and probabilistic bounds.
- Change budgets and temporal pressure must be respected (no unbounded exploration).
- Regime classification must include hysteresis to avoid oscillations.
- Stability enforcement MUST occur during pipeline execution.
- No decision may bypass the gate fusion layer.

## 1.1 Pipeline Execution Invariants

- Pipeline execution MUST be deterministic:
  - identical input + context → identical output

- Pipeline stages MUST:
  - be side-effect free
  - be independently executable

- Pipeline execution MUST be scheduler-compatible:
   - execution MAY be iterative (stage-by-stage)
   - iterative execution MUST be equivalent to full execution

- A pipeline execution is finalized ONLY when:
  - `completed=True`

- Partial execution MUST NOT:
  - produce terminal decisions
  - alter decision validity

- Iterative execution MUST:
  - produce identical results as full execution

---

## 2. Cognitive Bundle Invariants

- The bundle must be **immutable** (frozen dataclass or equivalent).
- **No prescriptive fields** allowed (no actions, recommendations, "should", "execute", "next_step").
- Explanations must be purely declarative (no causal language: "because", "therefore", "we decided").
- Timeline entries inside the bundle must not include ACTION_* types.
- Context hints limited to shallow primitives (str, bool, int, float, None — no nesting or profiling).
- No callables or hidden logic inside the bundle.
- MemoryLong must be passive (no mutation methods exposed).
- Invariants must be validated on construction (raise on violation).
- Runtime MUST NOT mutate bundle contents after construction.
- Bundle MUST be independent from scheduler execution:
   - construction MUST NOT depend on execution order

## 2.1 Canonical Cognitive State Invariants

- `CognitiveState` must be deterministic and serializable.
- Exported state values must respect bounded, normalized contracts.
- Canonical state must be suitable for IR export without hidden runtime mutation.
- Contract validation must happen before externalization whenever applicable.
- Canonical state MUST be independent from runtime execution order.

## 3. Cognitive Timeline Invariants

- Append-only journal — no mutation of past entries.
- Entries classified as STATE (introspection, uncertainty, governance) or EVENT (observed facts).
- Signal types are **closed registry** (finite, explicit, versioned).
- Supersession is deterministic and read-only (older → newer via version).
- Canonical mapping enforced (every signal type/version → fixed category/code/state).
- All entries must be traceable to originating bundle or post-cognitive source.
- Scheduler events MUST be traceable (enqueue, execution, completion, abort).
- Timeline MUST preserve execution ordering:
  - scheduler ordering MUST be reconstructible
  - execution causality MUST be replayable

## 4. Reflexive Snapshot & Self-Model Invariants

- ReflexiveSnapshot must be frozen and filtered (public views only).
- Self-description must combine snapshot + attestation (rendered payload).
- No self-modification or hidden inference allowed.
- Capabilities and principles are declarative and attested.
- Timeline exposure explanation must be built-in and declarative.
- Runtime state MUST be introspectable through reflexive interfaces.

## 5. Conversation Orchestration Invariants (partial v0.1)

- Collapse guard must detect and prevent divergence.
- Attractor model must maintain coherence.
- Regime switching must be hysteresis-protected.
- Stability controller must enforce coherence bounds.
- Conversation orchestration MUST remain independent from scheduler execution.

**Violation of any invariant results in rejection or non-compliance.**