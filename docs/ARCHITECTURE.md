# ARVIS Architecture

## Overview

ARVIS is a **deterministic Cognitive Operating System with a kernel-based architecture**.

It is implemented around:

- a **Kernel Core Layer** (processes, scheduler, syscalls, interrupts)
- a **deterministic cognitive pipeline** (decision system)
- a **canonical state system**
- a **reflexive self-observation layer**

ARVIS behaves as a **cognitive execution kernel**:

> cognition is constructed, evaluated, regulated, and only then allowed to produce a validated intent.

It enforces:

* structured cognition
* stability-constrained decision-making
* full traceability of execution

ARVIS is not a model architecture.

It is a **cognitive execution system** where:

> cognition is constructed, evaluated, regulated, and only then allowed to produce a validated intent (which may result in an action).

---

## Core Architectural Principle

> ARVIS does not generate decisions.
> It determines whether a decision is **allowed to be executed under stability constraints**.

---

## System Model

ARVIS is implemented as a deterministic system with the following architectural domains:

0. kernel core (process / scheduler / syscalls / interrupts)
1. kernel services (domain services: VFS, ZIP, memory, etc.)
2. cognitive execution (pipeline)
3. runtime execution (side-effects via syscalls)
4. canonical state
5. public contract / IR 
6. reflexive observation
7. conversation & response layer
8. interoperability / canonical projection

---

### Execution Flow

```text
Input
  → Process creation (Kernel)
  → Scheduler selection
  → Pipeline execution (stage-by-stage)
  → Canonical CognitiveState
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
- `PipelineExecutor`
- `ResourcePressure`

Execution model:

- tick-based scheduling
- one execution step per tick
- preemptive execution
- deterministic selection

Important:

> The runtime does NOT define cognition.
> It only orchestrates execution.

This creates a strict separation:

- runtime → execution control
- pipeline → decision semantics

Execution flow detail:

```text
tick:
  → select process
  → PipelineExecutor.execute_process()
      → run_stage OR finalize_run
  → update process state
```

---

## Cognitive Pipeline 

The pipeline remains the **execution core**, but it is no longer the whole system.

Its outputs are normalized into a **canonical CognitiveState** and may then be

exported through IR or observed through reflexive services.

The pipeline is executed under the control of the Kernel Core.

It may run:

- as a full execution (single step)
- or incrementally across multiple scheduler ticks

---

### Pipeline Execution Contract 

The pipeline is executed under a strict runtime contract:

- execution is stage-by-stage (iterative)
- only one stage is executed per scheduler tick
- stages are non-terminal by definition
- pipeline completion is ONLY allowed via `finalize_run()`

The execution flow is:

```text
Scheduler → PipelineExecutor → run_stage() → ... → finalize_run()
```

Rules:

- run_stage() MUST NOT produce a final decision
- finalize_run() MUST produce a non-null terminal result
- any violation results in runtime error

This ensures:

- deterministic execution
- safe preemption
- no implicit decision leakage

---

## Canonical State Layer

This layer defines the stable internal state contract of ARVIS:

- CognitiveState
- CognitiveStateBuilder
- CognitiveStateContract
- StateIRAdapter

It is the bridge between execution and external interoperability.

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

- injects memory signals
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

---

## Memory System

ARVIS includes a structured memory subsystem.

Components:

- long-term memory registry
- memory policy gates
- memory projection into cognition and conversation

Memory can:
- inject contextual signals
- constrain decisions
- constrain response strategies (without introducing new semantics)

Memory is integrated at:

- pipeline level (state construction)
- conversation level (response shaping)

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
- Pipeline Executor → controls HOW cognition runs
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

(runtime execution handled outside pipeline)

(see `cognitive_pipeline.py`) 

---

## Closed-Loop Control Structure (CRITICAL)

ARVIS implements a **closed-loop control system**:

```text
Scheduler
→ PipelineExecutor
→ Pipeline (stages)
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

---

## Key Insight

> ARVIS is not a layered architecture.
> It is a **closed-loop cognitive dynamical system implemented as a pipeline**.

---

## Logical Components (Functional View)

Although implemented as a pipeline, ARVIS can be decomposed into functional roles:

### 0. Execution Orchestration

* CognitiveScheduler
* Process lifecycle management

→ ensures deterministic execution ordering

---

### 1. State Construction

* Bundle Stage
* Context + memory aggregation

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
* Pipeline execution progression (stage index, lifecycle)
* Runtime execution (side-effects)
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

---

## Trace & Replay

Each execution produces:

* a **DecisionTrace**
* a structured timeline entry

Properties:

* deterministic
* replayable
* auditable

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

### Role

The IR provides:

- a stable system output
- a decoupling layer between cognition and execution
- a bridge for external integrations (LLM, APIs, replay systems)

IMPORTANT:

IR is the canonical internal representation of ARVIS.

- IR is expressive, extensible, and system-oriented
- CanonicalSignals are constrained, registry-bound, and external

The Kernel Adapter is responsible for transforming IR into canonical signals.

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

---

## Relation to ARVIS OS Standard

ARVIS architecture aligns with the Cognitive OS standard:

* Kernel Layer → Kernel Core (scheduler / process / syscalls)
* Cognition Layer → Cognitive Pipeline
* Execution Layer → Syscall Execution
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
