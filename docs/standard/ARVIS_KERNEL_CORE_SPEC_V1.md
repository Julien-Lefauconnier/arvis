# ARVIS Kernel Core

## Overview

The ARVIS Kernel Core is the **execution authority of the Cognitive Operating System**.

It is responsible for:

- process lifecycle management
- scheduling
- execution control
- syscall dispatching
- interrupt handling

It behaves analogously to an operating system kernel.

---

## Core Principle

> The Kernel executes cognition but does NOT define cognition.

- Cognition is defined by the **Cognitive Pipeline**
- Execution is controlled by the **Kernel Core**

---

## Responsibilities

The Kernel Core defines:

- which process executes
- when execution occurs
- how execution is interrupted or resumed
- how side-effects are triggered (via syscalls)

It enforces:

- deterministic execution
- safe preemption
- strict separation between cognition and execution

---

## Kernel Architecture

The Kernel Core is composed of four subsystems:

1. **Process System**
2. **Scheduler**
3. **Syscall System**
4. **Interrupt System**

---

# 1. Process System

## Overview

The process system manages **cognitive execution units**.

Each user request is executed as a **CognitiveProcess**.

---

## CognitiveProcess

Represents an isolated execution unit.

### Properties

- `process_id`
- `user_id`
- `status`
- `priority`
- `budget`
- `local_state` (pipeline context)
- `last_result`
- `last_error`

---

## Process Lifecycle

A process transitions through the following states:

```text
READY
→ RUNNING
→ (PREEMPTED | WAITING_CONFIRMATION | BLOCKED | SUSPENDED)
→ COMPLETED
```

### State Definitions

- READY: eligible for execution
- RUNNING: currently executing
- WAITING_CONFIRMATION: blocked on user input
- PREEMPTED: paused due to scheduling
- BLOCKED: waiting for external event
- SUSPENDED: paused indefinitely
- COMPLETED: execution finished

---

## Process Factory

Processes are created via:

```python
ProcessFactory.create(...)
```

This ensures:

- consistent initialization
- deterministic process identity
- proper runtime configuration

---

## Process Budget

Each process is constrained by a CognitiveBudget:

- reasoning steps
- time slice (ms)

Purpose:

- prevent unbounded execution
- enforce fairness
- ensure system stability

---

## Process Priority

Each process has a priority score:

```python
CognitivePriority(value: float)
```

Used by the scheduler for selection.

---

# 2. Scheduler

## Overview

The scheduler is responsible for execution ordering.

It selects which process runs at each tick.

---

## CognitiveScheduler

Core component controlling execution.

### Responsibilities

- process selection
- queue management
- preemption
- fairness enforcement

---

## Execution Model

Execution is tick-based:

```text
tick:
  → select process
  → execute one step
  → update state
```

---

## Deterministic Scheduling

The scheduler MUST be deterministic:

- same inputs → same execution order
- no randomness
- reproducible execution

---

## Preemption

The scheduler supports preemption:

- processes may be paused between stages
- execution resumes later without state loss

---

## Scheduling Constraints

The scheduler MUST:

- respect process priority
- respect execution budgets
- preserve determinism

The scheduler MUST NOT:

- modify cognitive results
- inject decisions
- alter pipeline semantics

---

# 3. Syscall System

## Overview

The syscall system is the only mechanism for side-effects.

All external interactions MUST go through syscalls.

---

## Core Principle

    No side-effect is allowed outside the syscall layer.

---

## SyscallHandler

Central dispatcher:

```python
SyscallHandler.handle(Syscall)
```

Responsibilities:

- route syscall to implementation
- execute safely
- record results

---

## Syscall Structure

A syscall is defined as:

```python
Syscall(
    name: str,
    args: dict
)
```

---

## Syscall Result

```python
SyscallResult(
    success: bool,
    result: Any,
    error: Optional[str]
)
```

---

## Built-in Syscalls

Examples:

- tool.execute
- process.*
- memory.*
- interrupt.*

---

## Tool Execution

Tool execution is performed via:

```python
tool.execute syscall
```

Important:

- tools are NOT part of cognition
- tools are executed AFTER pipeline completion
- results are recorded in ctx.extra["syscall_results"]

---

## Syscall Journal

All syscalls are recorded:

```python
ctx.extra["syscall_results"]
```

This ensures:

- full traceability
- replayability
- auditability

---

## Constraints

Syscalls MUST:

- be deterministic (given same inputs)
- be observable
- be isolated from cognition

Syscalls MUST NOT:

- alter pipeline logic
- modify decision semantics

---

# 4. Interrupt System

## Overview

The interrupt system enables runtime control over execution flow.

---

## Core Components

- Interrupt
- InterruptBus
- InterruptType

---

## Purpose

Interrupts allow:

- process suspension
- external signaling
- coordination between runtime components

---

## Constraints

Interrupts MUST:

- affect execution flow ONLY
- NOT modify cognitive state
- NOT inject decisions

---

## Example Use Cases

- pause execution
- resume process
- trigger external event handling

---

# Kernel Execution Flow

Full execution flow:

```text
User Input
→ ProcessFactory.create
→ Scheduler.enqueue
→ Scheduler.tick
    → select process
    → PipelineExecutor.execute_stage
→ (repeat until completion)
→ finalize_run()
→ Syscall execution (if needed)
→ process completed
```

---

# Separation of Concerns

| Layer       | Responsibility  |
| ----------- | --------------- |
| Pipeline    | Cognition       |
| Kernel Core | Execution       |
| Syscalls    | Side-effects    |
| IR          | Output contract |

---

# Determinism Guarantees

The Kernel Core ensures:

- deterministic scheduling
- deterministic process transitions
- deterministic syscall recording

This guarantees:

- replayability
- auditability
- reproducibility

---

# Safety Guarantees

The Kernel enforces:

- no execution without validation
- no side-effects outside syscalls
- no cognitive mutation at runtime level
- bounded execution via budgets

---

# Replay Compatibility

The Kernel is compatible with replay systems:

- process execution is deterministic
- syscall journal is recorded
- timeline can be reconstructed

---

# Design Principles

## 1. Execution Isolation

Cognition and execution are strictly separated.

---

## 2. Deterministic Control

All execution decisions are reproducible.

---

## 3. Explicit Side-Effects

All side-effects go through syscalls.

---

## 4. Safe Preemption

Execution may pause at any time without corruption.

---

## 5. Full Traceability

All actions are recorded and auditable.

---

# Summary

The ARVIS Kernel Core is:

    a deterministic execution engine
    controlling processes, scheduling, and side-effects

It ensures that:

- cognition is executed safely
- execution is controlled and observable
- side-effects are strictly regulated

The Kernel Core is the foundation that enables ARVIS to behave as a true Cognitive Operating System.