# ARVIS Architecture

## Overview

ARVIS is a **deterministic Cognitive Operating System with a kernel-based architecture**.

It is implemented around:

- a **Kernel Core Layer** (processes, scheduler, syscalls, interrupts)
- a **runtime orchestration layer** (`CognitiveRuntime`)
- a **modular deterministic cognitive pipeline** (decision system)
- a **canonical state system**
- a **reflexive self-observation layer**

```text
Kernel Core
   ↓
Runtime Orchestration
   ↓
Cognitive Pipeline
   ↓
Canonical State / IR
   ↓
Conversation / Response
   ↓
Syscalls / Side Effects
   ↓
Timeline / Reflexive / Projection
```

ARVIS behaves as a **cognitive execution kernel**:

It enforces:

* structured cognition
* stability-constrained decision-making
* full traceability of execution

> cognition is constructed, evaluated, regulated, and only then allowed to produce a validated intent (which may result in an action).

ARVIS is not a model architecture.  
It is a **cognitive execution system**.

---

## Core Architectural Principle

> ARVIS does not generate decisions.
> It determines whether a decision is **allowed to be executed under stability constraints**.

---

## System Model

ARVIS is implemented as a deterministic system with the following architectural domains:

0. kernel core (process / scheduler / syscalls / interrupts)
1. kernel services (domain services: VFS, ZIP, memory, etc.)
2. runtime orchestration (`CognitiveRuntime`)
3. cognitive execution (pipeline services)
4. runtime execution (side-effects via syscalls)
5. canonical state
6. public contract / IR 
7. reflexive observation
8. conversation & response layer
9. interoperability / canonical projection

These domains are intentionally separated so that:

- cognition remains deterministic
- execution remains observable
- memory remains policy-controlled
- external integrations remain non-authoritative
- replay remains verifiable

---

## Kernel Resources

ARVIS defines explicit kernel-managed resources:

- Processes (execution units)
- VFS (structured data namespace)
- Memory (cognitive continuity and constraints)

These resources are:

- accessed via syscalls
- mediated through kernel services
- strictly controlled by the Kernel Core

---

### Execution Flow

```text
Input
  → Process creation (Kernel)
  → Scheduler selection
  → Pipeline execution (stage-by-stage)
  → Canonical CognitiveState / PipelineResult
  → Decision (validated / abstained)
  → Intermediate Representation (IR)
  → Conversation Layer
  → Response Plan
  → (Optional) Realization
  → Syscall Layer (tool execution / side-effects)
  → Observability / Trace / Timeline
  → Reflexive Snapshot
  → Canonical Projection (Kernel Adapter)
  → Public API
```

IMPORTANT:
The IR defines the canonical boundary between cognition and response construction.

This boundary is critical:

- cognition ends before rendering begins
- side-effects occur after decision validation
- replay can reconstruct decisions independently of execution

---

## Kernel Core Layer

The Kernel Core is the **execution authority of ARVIS**, analogous to an operating system kernel.

It is responsible for:

- process lifecycle management
- scheduling decisions
- execution control
- syscall handling
- interrupt handling

Core components:

- `CognitiveScheduler`
- `CognitiveProcess`
- `ProcessFactory`
- `SyscallHandler`
- `InterruptBus`

### Responsibilities

The Kernel Core defines:

- which process executes
- when execution occurs
- how execution is interrupted or resumed
- how side-effects are triggered (via syscalls)

### Key Principle

> The Kernel executes cognition but does NOT define cognition.

It enforces:

- deterministic scheduling
- safe preemption
- strict execution boundaries
- isolation of side-effects

### Execution Model

- tick-based scheduling
- preemptive execution
- process states (READY / RUNNING / WAITING / COMPLETED)
- syscall-based side-effect execution

The Kernel Core is the only layer allowed to trigger execution and side-effects.

---

## Kernel Services Layer

The Kernel Services Layer contains all domain-specific logic used by syscalls.

It is accessed exclusively via:

```python
KernelServiceRegistry
```

Core kernel services include:

- VFS Service
- ZIP Ingest Service
- Memory Service

### Responsibilities

- implement business logic (VFS, ZIP ingestion, memory, etc.)
- encapsulate stateful operations
- provide deterministic service interfaces

### Properties

- explicitly injected into the kernel
- no global state
- partially available (services may be None)
- fully testable via stubs

### Separation of Concerns

| Layer    | Responsibility      |
| -------- | ------------------- |
| Syscalls | execution interface |
| Services | domain logic        |


This ensures:

- clean architecture
- test isolation
- deterministic behavior
- graceful degradation when optional services are unavailable

---

## Kernel Scheduling Layer

This layer is part of the Kernel Core.

It is responsible for:

- process scheduling
- execution ordering
- preemption
- budget enforcement


Core components:

- `CognitiveScheduler`
- `CognitiveProcess`
- `CognitiveRuntimeState`
- `CognitiveRuntime`
- `ResourcePressure`

Execution model:

- tick-based scheduling
- one execution step per tick
- preemptive execution
- deterministic selection

Important:

> The runtime does NOT define cognition.
> It only orchestrates execution.

This means scheduler behavior can evolve independently from decision semantics.

This creates a strict separation:

- runtime → execution control
- pipeline → decision semantics

Execution flow detail:

```text
tick:
  → select process
  → CognitiveRuntime.execute(ctx)
      → scheduler/process orchestration
      → pipeline execution service
      → result finalization
  → update process state
```

---

## Cognitive Pipeline 

The pipeline remains the **execution core**, but it is no longer the whole system.

Its outputs are normalized into a **canonical CognitiveState** and a public
CognitiveResultView, then exported through **IR** or observed through reflexive
services.

The pipeline is executed under the control of the Kernel Core.

It may run:

- as a full execution (single step)
- or incrementally across multiple scheduler ticks

The pipeline implementation is now decomposed into explicit services:

- bootstrap services
- input preparation services
- stage registry services
- stage execution services
- iteration services
- lifecycle services
- replay services
- IR services
- observability services
- result and trace factories

This decomposition keeps CognitivePipeline as the orchestration façade while
moving specialized responsibilities into dedicated, testable modules.

Benefits:

- lower coupling
- easier testing
- clearer ownership boundaries
- faster future refactors

---

### Pipeline Execution Contract 

The pipeline is executed under a strict runtime contract.

The public execution path is:

```text
CognitiveOS
 CognitiveRuntime
 CognitivePipeline
 Pipeline services
 CognitiveResultView / IR
```

The lower-level execution contract remains:

- execution is stage-by-stage (iterative)
- only one stage is executed per scheduler tick
- stages are non-terminal by definition
- pipeline completion is ONLY allowed via `finalize_run()`

The execution flow is:

```text
Scheduler / Runtime → Pipeline services → run_stage() → ... → finalize_run()
```

Rules:

- run_stage() MUST NOT produce a final decision
- finalize_run() MUST produce a non-null terminal result
- any violation results in runtime error

This ensures:

- deterministic execution
- safe preemption
- no implicit decision leakage
- identical semantics between iterative and full execution

---

## Canonical State Layer

This layer defines the stable internal state contract of ARVIS:

- CognitiveState
- CognitiveStateBuilder
- CognitiveStateContract
- StateIRAdapter

It is the bridge between execution and external interoperability.

The canonical state transforms transient runtime artifacts into a stable internal truth model.

---

## Public API Layer

The public API layer exposes the stable entrypoint:

```python
CognitiveOS
```

CognitiveOS is now intentionally thin.

It is responsible for:

- tool registration
- public execution methods
- IR export
- replay entrypoints
- result inspection
- multi-input execution

Internal execution logic is delegated to:

```python
CognitiveOSInternals
CognitiveRuntime
CognitiveResultView
```

This preserves a stable public contract while keeping runtime, replay, IR,
formatting, and trace construction outside the public façade.

Important:

> api/os.py is a public façade, not the runtime implementation.

This allows internal refactors without breaking public integrations.

---

## Conversation & Response Layer

This layer transforms a **validated cognitive decision** into a **controlled response**.

It is responsible for:

- selecting a response strategy
- integrating memory constraints
- adapting to conversational context
- constructing a structured response plan

Core components:

- `ConversationOrchestrator`
- `ResponseStrategyDecision`
- `ResponsePlan`
- `LinguisticAct`

### Responsibilities

1. Strategy Selection

Maps CognitiveIR (+ authorized context) → response strategy

- ABSTENTION
- CONFIRMATION
- INFORMATIONAL
- ACTION

2. Memory Integration

- applies memory-derived constraints and preferences
- constrains actions
- influences strategy selection

3. Adaptive Control

- reacts to instability signals
- adjusts response behavior dynamically

4. Response Planning

Builds a `ResponsePlan`:

- defines act type
- defines structure of response
- prepares realization phase

IMPORTANT:

> This layer does NOT perform cognition.  
> It transforms validated cognition into a safe communicable form.

This separation allows language generation to change without changing decisions.

---

## Realization Layer

This layer converts a `ResponsePlan` into an actual output.

It supports:

- template-based rendering
- controlled LLM generation

Components:

- `RealizationService`
- `PromptBuilder`
- `LLMExecutor`

IMPORTANT:

- LLMs are NOT part of cognition
- LLMs are NOT decision makers
- they only realize a pre-validated plan

This guarantees:

> generation is always constrained by cognition

LLMs are optional realizers, never authorities.

---

## Kernel Memory Subsystem

ARVIS includes a **kernelized memory subsystem**, implemented as part of the Kernel Core.

Memory is a **first-class kernel resource**, equivalent in architectural role to:

- VFS (structured namespace)
- Syscalls (execution boundary)

It provides:

- deterministic long-term memory storage
- policy-controlled access
- snapshot-based execution semantics
- syscall-based mutation

Memory is a governed kernel resource, not a free-form context store.

---

### Memory Architecture

The memory subsystem follows a strict execution pipeline:

```text
Repository → Policy → Projection → Snapshot
```

Where:

- Repository = storage layer (no policy)
- Policy = filtering (revoked / expired / visibility)
- Projection = execution view
- Snapshot = deterministic, immutable representation

---

### Kernel Integration

Memory is exposed through:

```python
KernelServiceRegistry.memory_service
```

All memory access MUST go through the memory service.

- Direct repository access is forbidden.

---

### Pipeline Integration

Memory is injected into the pipeline as a read-only snapshot:

```text
CognitivePipelineContext.long_memory_snapshot
```

Constraints:

- snapshot is immutable during execution
- no stage may mutate memory
- memory influences decision but does not redefine cognition

---

### IR Exposure

Memory is NOT exposed directly in IR.

Only derived constraints are allowed:

```json
{
  "long_memory_constraints": [...],
  "long_memory_preferences": {...}
}
```

---

### Key Principle

  Memory constrains cognition.
  It does NOT introduce new semantics.

This preserves determinism and prevents hidden knowledge injection.

---

### Mutation Model

Memory mutations occur exclusively via syscalls:

- memory.write
- memory.revoke

They are:

- post-decision
- replay-safe
- fully observable

---

### Summary

Memory in ARVIS is:

- deterministic
- policy-controlled
- snapshot-based
- kernel-managed

---

## Reflexive Layer

The reflexive layer is read-only and declarative.

It includes:

- capability registry and snapshots
- architecture / cognition / runtime / uncertainty introspection
- reflexive rendering
- reflexive snapshot building
- reflexive timeline aggregation and explanation
- compliance and attestation

This layer does not perform cognition. It observes and exposes structure safely.

It exists for transparency, debugging, compliance, and operator trust.

---

## Syscall Execution Layer

This layer executes **side-effects AFTER decision finalization**.

This layer is consistent with the Decision Specification, the Pipeline Specification, and the execution-level constraints defined in the specification hierarchy.

It is distinct from the runtime orchestration layer.

Responsibilities:

- tool execution
- adapter hosting
- external system interaction

This layer operates AFTER:

- decision validation
- response planning
- (optional) response realization

It executes:

- tools
- external actions

Important:

- this layer is NOT part of cognition
- this layer is NOT the scheduler (orchestration is handled separately)

It operates strictly after the decision pipeline.

Clarification:

- Kernel Scheduling Layer → controls WHEN cognition runs
- Pipeline services → control HOW cognition runs
- Syscall Execution Layer → executes actions AFTER cognition

These three layers are strictly separated.

All side-effects are executed through syscalls.

This includes:

- tool execution
- external interactions
- adapter calls

This layer is:

- strictly post-decision
- fully observable
- replay-safe (no re-execution)
- replaceable without affecting cognition

---

## Interrupt System 

ARVIS supports an interrupt mechanism for runtime control.

Interrupts allow:

- process suspension
- external signaling
- runtime coordination

Core components:

- `Interrupt`
- `InterruptBus`
- `InterruptType`

Constraints:

- interrupts MUST NOT alter cognitive semantics
- interrupts only affect execution flow

---

## Kernel Adapter Layer 

The Kernel Adapter Layer enables interoperability between ARVIS IR and external canonical signal systems (e.g. Veramem Kernel).

The Kernel Adapter Layer introduces a semantic fingerprinting mechanism to guarantee deterministic equivalence of signals
across executions, independent of runtime metadata.

This layer is responsible for:

- mapping CognitiveIR → CanonicalSignals
- applying deterministic projection rules (no decision logic)
- ensuring compatibility with external canonical registries
- preserving semantic determinism and replayability
- enforcing closed-world signal validity (via registry)

Semantic equivalence of projected signals MUST be evaluated using a canonical fingerprinting mechanism defined at the adapter level.

This ensures replay compatibility independent of runtime metadata.

### Structure

- `ir_to_canonical.py` → IR → signals mapping
- `rules/` → rule-based emission system
- `signal_factory.py` → canonical signal construction
- `kernel_adapter.py` → orchestration layer

### Design Principles

- deterministic mapping
- no hidden logic
- rule-based extensibility
- strict separation from cognitive pipeline
  - no interpretation or policy resolution
  - no side-effects or execution logic
  - canonical registry compliance (closed-world assumption)

IMPORTANT:

This layer is NOT part of cognition.
It is a **a canonical projection layer for interoperability**.

It does NOT:

- make decisions
- resolve conflicts
- apply business or cognitive logic
- influence the cognitive pipeline

It ONLY:

- projects already-computed cognition into a canonical external representation
- enforces compatibility with external signal systems

This guarantees that:

> cognition remains inside ARVIS,
> while canonical truth validation remains external.

This is the foundation of ARVIS ↔ Veramem interoperability.

---

### Pipeline Structure

The system executes a fixed sequence of stages:

Tool Interaction Stages:

0. ToolFeedback Stage
1. ToolRetry Stage

Core Cognitive Stages:

2. Decision Stage
3. Passive Context Stage
4. Bundle Stage
5. Conflict Stage
6. Core Stage
7. Regime Stage
8. Temporal Stage
9. Conflict Modulation Stage
10. Control Stage
11. Projection Stage
12. Gate Stage
13. Control Feedback Stage
14. Structural Risk Stage
15. Confirmation Stage
16. Execution Stage
17. Action Stage
18. Intent Stage

Execution Boundary:

19. Syscall Execution (non-cognitive layer)

Runtime execution is handled outside the pipeline by CognitiveRuntime.

Pipeline orchestration is exposed by cognitive_pipeline.py, while the
implementation is delegated to kernel/pipeline/services/ and
kernel/pipeline/factories/

---

## Closed-Loop Control Structure (CRITICAL)

ARVIS implements a **closed-loop control system**:

```text
Scheduler
→ CognitiveRuntime
→ Pipeline services / stages
→ Control
→ Gate
→ Control Feedback
→ Control
→ (loop across scheduler ticks)
```

### Roles

* **Control Stage**

  * sets exploration / epsilon
  * adjusts decision aggressiveness

* **Gate Stage**

  * enforces stability constraints
  * filters unsafe decisions

* **Control Feedback Stage**

  * updates control based on Gate outcome
  * closes the feedback loop

This architecture makes ARVIS a regulated dynamical system rather than a static inference pipeline.

---

## Key Insight

> ARVIS is not a layered architecture.
> It is a **closed-loop cognitive dynamical system implemented as a pipeline**.

> Memory is not a passive data store.
> It is a kernel-governed constraint system influencing cognition under strict policy control.

> Execution is not cognition.
> Generation is not reasoning.

---

## Logical Components (Functional View)

Although implemented as a pipeline, ARVIS can be decomposed into functional roles:

### 0. Execution Orchestration

* CognitiveScheduler
* CognitiveRuntime
* Process lifecycle management

→ ensures deterministic execution ordering

---

### 1. State Construction

* Bundle Stage
* Context + memory snapshot integration (read-only)

→ produces an **explicit cognitive state**

---

### 2. Scientific Modeling

* Core Stage
* Regime Stage
* Temporal Stage

→ computes:

* risk
* drift
* system regime
* stability signals

---

### 3. Control System

* Control Stage
* Control Feedback Stage

→ adjusts system behavior dynamically

---

### 4. Stability Enforcement

* Gate Stage
* Structural Risk Stage

→ ensures:

* unsafe decisions are blocked
* unstable states cannot propagate

---

### 5. Decision Finalization (Cognitive Output)

* Confirmation Stage
* Execution Stage
* Action Stage
* Intent Stage

→ produces a **validated cognitive intent**, not a final user response

---

### 6. System Update

* Runtime orchestration (scheduler state)
* Pipeline service progression (stage index, lifecycle)
* Runtime execution and syscall boundaries
* timeline integration

→ updates internal state and timeline after execution

---

## Observability Layer (Post-Execution)

After pipeline execution:

* system state is projected
* stability metrics are computed
* predictions and statistics are derived

This layer is:

* read-only
* non-causal (does not influence decisions)

It enables metrics, forecasting, debugging, and audits without contaminating cognition.

---

## Trace & Replay

Each execution produces:

* a **DecisionTrace**
* a structured timeline entry

Properties:

* deterministic
* replayable
* auditable
* hash-verifiable

---

## Determinism Guarantees

ARVIS ensures:

* fixed execution order
* no hidden branching
* fail-soft execution
* deterministic outputs (given same input)

This includes:

- scheduler decisions
- process transitions
- pipeline execution steps
- replay commitment verification
- IR export

---

## Intermediate Representation (IR)

ARVIS introduces an **Intermediate Representation (IR)** layer.

This layer sits between the kernel and the external API:

```
Pipeline → Result → IR → Canonical Projection → API
```

### Properties

- deterministic
- serializable
- model-agnostic
- replayable
- stable across internal refactors

### Role

The IR provides:

- a stable system output
- a decoupling layer between cognition and execution
- a bridge for external integrations (LLM, APIs, replay systems)

IR can be produced through:

```python
CognitiveOS.run_ir(...)
CognitiveResultView.to_ir()
```

IMPORTANT:

IR is the canonical internal representation of ARVIS.

- IR is expressive, extensible, and system-oriented
- CanonicalSignals are constrained, registry-bound, and external

The Kernel Adapter is responsible for transforming IR into canonical signals.

IR is the long-term contract surface of ARVIS.

---

## Architectural Guarantees

The system enforces:

* no direct execution without validation
* explicit cognitive state construction
* stability constraints before action
* bounded and normalized signals
* full decision traceability
* strict separation between cognition and canonical projection
* no policy or decision logic outside the cognitive pipeline
* public API façade separated from runtime internals
* pipeline orchestration separated from pipeline services
* replay verification separated from replay execution
* cognition separated from language realization
* cognition separated from tool execution
* canonical state separated from runtime artifacts

---

## Relation to ARVIS OS Standard

ARVIS architecture aligns with the Cognitive OS standard:

* Kernel Layer → Kernel Core (scheduler / process / syscalls)
* Cognition Layer → Cognitive Pipeline
* Runtime Layer → CognitiveRuntime
* Execution Layer → Syscall Execution / ToolExecutor
* API Layer → CognitiveOS

(see ARVIS_STANDARD_V1.md) 

---

## Summary

ARVIS is:

> a deterministic cognitive runtime system
> implementing a closed-loop control system
> where decisions are:
>
> constructed → evaluated → constrained → allowed → executed

It is not a passive architecture.

It is an **active stability-enforcing system**.

It is designed for:

- auditable AI systems
- deterministic tool-use systems
- replayable cognitive runtimes
- safety-constrained autonomous architectures