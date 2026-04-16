# ARVIS Kernel Services Specification V1

## Overview

The Kernel Service Layer defines how core services are structured, injected, and accessed within ARVIS.

It acts as the internal backbone of the Kernel Core, enabling controlled interaction between syscalls and domain services.

---

## Core Principle

> All services MUST be accessed through the KernelServiceRegistry  
> and MUST enforce domain-level policies and invariants.

This ensures:
- deterministic behavior
- explicit dependency injection
- testability
- no hidden coupling

Services are not simple utilities.

They are the **authoritative enforcement layer** for:

- domain constraints
- access control
- mutation validity
- system invariants

---

## Architecture

Pipeline → Kernel → Syscalls → Services → Effects

---

## KernelServiceRegistry

Central container for all services:

```python
KernelServiceRegistry(
    vfs_service: Optional[VFSService],
    zip_ingest_service: Optional[ZipIngestService],
    memory_service: Optional[MemoryService],
)
```

### Properties

- Immutable during runtime
- Explicitly constructed
- No global access
- Supports partial availability (services can be None)

---

## Access Pattern

```python
def syscall(handler, ...):
    service = handler.services.vfs_service
```

Rules:
- Always check for None
- Never instantiate services inside syscalls

Syscalls MUST NOT:

- bypass services
- access storage directly
- embed domain logic

---

## Service Types

### 1. Domain Services
Examples:
- VFSService
- ZipIngestService

Responsibilities:
- business logic
- controlled state transitions
- enforcement of domain invariants
- orchestration of subcomponents

---

### 2. Sub-Services

Example (ZipIngestService):
- analyzer
- planner
- executor
- collision_service

Properties:
- internal to service
- not exposed via registry
- must be stubbed in tests if used indirectly

---

### MemoryService

The MemoryService is responsible for:

- controlled memory mutations
- policy enforcement (scope, consent, retention)
- validation of memory writes and revocations

It is the ONLY component allowed to:

- persist memory
- modify long-term storage

IMPORTANT:

The pipeline NEVER accesses MemoryService directly.

Memory is injected into cognition via snapshots.

---

## Lifecycle

Services are:

- created at kernel initialization
- injected into registry
- reused across syscalls

---

### State Model

Services may be:

- stateless (pure logic)
- stateful (managing controlled persistence)

Stateful services MUST:

- enforce strict mutation policies
- remain deterministic given same inputs

---

## Execution Role

Kernel Services operate strictly in the execution phase:

```text
Pipeline → finalize_run → IR → Kernel → Syscalls → Services
```

They:

- execute validated operations
- enforce domain constraints
- interact with external systems

They do NOT:

- initiate execution
- participate in scheduling

---

## Testability Model

Tests inject stub services:

```python
handler = SyscallHandler(
    services=KernelServiceRegistry(
        vfs_service=StubVFS(),
        zip_ingest_service=StubZip(),
    )
)
```

Important:
- stubs must implement used attributes
- including nested dependencies (planner, executor...)

---

## Constraints

Services MUST:
- be deterministic
- be side-effect controlled
- expose clear interfaces

Services MUST NOT:
- depend on global state
- mutate registry
- perform hidden I/O
- expose repositories directly
- allow direct persistence access
- bypass validation layers

---

## Separation from Cognition

Kernel Services are strictly outside cognition.

They:

- do NOT participate in reasoning
- do NOT influence decision logic
- do NOT inject semantics into the pipeline

They only execute validated operations AFTER decision.

---

## Design Principles

1. Explicit Dependency Injection
2. No Global State
3. Test-First Design
4. Clear Separation of Concerns
5. Deterministic Execution
6. Policy Enforcement First
7. No Direct Data Access
8. Post-Decision Execution Only

---

## Summary

The Kernel Services Layer is:

a structured dependency system ensuring safe, testable, and deterministic execution of all kernel-level operations.

Kernel Services do not decide what should happen.

They enforce what is allowed to happen.
