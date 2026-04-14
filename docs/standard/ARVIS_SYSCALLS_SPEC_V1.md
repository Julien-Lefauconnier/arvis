# ARVIS Syscall System

## Overview

The ARVIS Syscall System is the **exclusive interface for all side-effects** in the Cognitive Operating System.

It provides a **controlled, deterministic, and observable mechanism** for:

- tool execution
- process management
- memory interaction
- runtime signaling

---

## Core Principle

> No side-effect is allowed outside the syscall system.

The syscall layer enforces:

- strict separation between cognition and execution
- explicit execution boundaries
- full traceability of all side-effects

---

## Position in Architecture

```text
Pipeline (Cognition)
    ↓
Validated Intent
    ↓
Kernel Core
    ↓
Syscall System
    ↓
External Effects (tools, memory, adapters)
```

---

## Syscall Lifecycle

```text
Decision → Action → Syscall → Execution → Result → Journal
```

Steps:

1. pipeline produces an executable intent
2. Kernel decides to execute a syscall
3. syscall is dispatched via SyscallHandler
4. syscall is executed safely
5. result is recorded in journal

---

## Syscall Model

### Syscall

```python
Syscall(
    name: str,
    args: dict
)
```

- name → syscall identifier
- args → execution payload

---

### SyscallResult

```python
SyscallResult(
    success: bool,
    result: Any = None,
    error: Optional[str] = None
)
```

Properties:

- success → execution outcome
- result → returned payload
- error → structured failure reason

---

### Syscall Handler

Central execution entrypoint:

```python
SyscallHandler.handle(syscall)
```

Responsibilities:

- resolve syscall implementation
- execute safely
- normalize output
- record execution result
- provide access to kernel services via ServiceRegistry

---

### Syscall Registry

Syscalls are registered via:

```python
@register_syscall("name")
def handler(...):
    ...
```

This ensures:

- explicit syscall definition
- no dynamic or hidden execution paths
- deterministic dispatch

---

## Syscall Categories

ARVIS defines multiple syscall domains:

### 1. Tool Syscalls

tool.execute

Executes a registered tool.

```text
Input:
- tool name
- payload

Output:
- tool result
```

Properties:

- tools are external to cognition
- execution occurs AFTER pipeline completion
- failures are captured, not thrown

Example:

```python
Syscall(
    name="tool.execute",
    args={
        "result": action_decision,
        "ctx": ctx
    }
)
```

---

### 2. Process Syscalls

Used to interact with process lifecycle.

Examples:

- process creation
- state transition
- scheduling signals

---

### 3. Memory Syscalls

Used for memory interaction:

- read memory
- write memory
- query long-term storage

IMPORTANT:

Memory syscalls MUST:

- respect memory policies
- remain deterministic (given same state)

---

### 4. Interrupt Syscalls

Used for runtime signaling:

- emit interrupt
- handle interrupt
- control execution flow

---

## Syscall Journal

All syscalls are recorded in:

```python
ctx.extra["syscall_results"]
```

Each entry contains:

```python
{
    "syscall": str,
    "success": bool,
    "result": Optional[Any],
    "error": Optional[str]
}
```

---

## Kernel Service Registry

 The Syscall System relies on a centralized service container:

```python
KernelServiceRegistry
```

This registry provides access to all kernel-level services used by syscalls.

Example services:

- VFSService
- ZipIngestService
- MemoryService (future)
- Tool adapters

---

### Purpose

The service registry ensures:

- explicit dependency injection
- isolation of syscall logic from service construction
- testability via service substitution (stubs/mocks)

---

### Access Pattern

Syscalls access services via the handler:

```python
def my_syscall(handler, ...):
    service = handler.services.my_service
```

---

### Properties

- services are optional (may be None)
- syscalls must handle missing services explicitly
- no global state access is allowed

---

## Properties

The syscall journal guarantees:

- full traceability
- replay compatibility
- auditability

---

## Determinism Guarantees

Syscalls MUST be:

- deterministic given same inputs
- observable
- replay-safe

Important:

- side-effects are NOT re-executed during replay
- only journal is used

---

## Error Handling

All syscall errors are:

- captured as SyscallResult(success=False)
- recorded in the journal
- exposed to the pipeline via ctx.extra

Errors MUST NOT:

- crash the runtime
- break pipeline execution

---

## Tool Retry Mechanism

Tool failures are handled via the pipeline:

1. syscall executes tool
2. failure recorded in journal
3. ToolFeedbackStage reads failure
4. ToolRetryStage may trigger retry

Key principle:

    Retry logic belongs to the pipeline, NOT the syscall layer.

---

## Execution Rules

Syscalls MUST:

- be explicitly triggered
- be fully observable
- produce structured results
- access external services ONLY via KernelServiceRegistry

Syscalls MUST NOT:

- be implicit
- modify cognitive reasoning
- inject decisions
- instantiate services directly
- access global singletons

---

## Security Model

The syscall layer enforces:

- controlled execution boundaries
- explicit authorization via pipeline
- isolation from cognitive logic

Future extensions:

- permission system
- sandboxed execution
- capability-based access control

---

## Replay Model

During replay:

- syscalls are NOT re-executed
- syscall results are replayed from journal

This guarantees:

- deterministic replay
- no external dependency

---

## Extension Model

New syscalls can be added via:

```python
@register_syscall("my.syscall")
def my_syscall(handler, ...):
    ...
```

Constraints:

- must be deterministic
- must return SyscallResult
- must be side-effect isolated

---

## Testability Model

The Service Registry enables controlled testing of syscalls.

Tests can inject stub services:

```python
handler = SyscallHandler(
    services=KernelServiceRegistry(
        vfs_service=StubVFSService(),
        zip_ingest_service=StubZipService(),
    )
)
```

This allows:

- deterministic unit testing
- isolation of syscall behavior
- validation of orchestration logic

---

Important:

Stubs must expose all attributes used by the syscall (including sub-services such as planners or executors).

---

## Design Principles

### 1. Explicit Execution

All side-effects must be explicit syscalls.

---

### 2. Full Observability

All executions are recorded.

---

### 3. Deterministic Replay

Execution can be replayed without re-triggering side-effects.

---

### 4. Separation of Concerns

| Layer    | Role              |
| -------- | ----------------- |
| Pipeline | Cognition         |
| Kernel   | Execution control |
| Syscalls | Side-effects      |

---

###  5. Fail-Safe Behavior

Failures are contained and recorded.

---

## Summary

The ARVIS syscall system is:

    a deterministic, observable execution interface
    ensuring all side-effects are controlled, traceable, and replay-safe

It is the foundation that allows ARVIS to safely interact with the external world while preserving cognitive integrity.