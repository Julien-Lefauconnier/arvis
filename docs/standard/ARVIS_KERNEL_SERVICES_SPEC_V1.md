# ARVIS Kernel Services Specification V1

## Overview

The Kernel Service Layer defines how core services are structured, injected, and accessed within ARVIS.

It acts as the internal backbone of the Kernel Core, enabling controlled interaction between syscalls and domain services.

---

## Core Principle

> All services MUST be accessed through the KernelServiceRegistry.

This ensures:
- deterministic behavior
- explicit dependency injection
- testability
- no hidden coupling

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

---

## Service Types

### 1. Domain Services
Examples:
- VFSService
- ZipIngestService

Responsibilities:
- business logic
- state manipulation
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

## Lifecycle

Services are:
- created at kernel initialization
- injected into registry
- shared across syscalls

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

---

## Design Principles

1. Explicit Dependency Injection
2. No Global State
3. Test-First Design
4. Clear Separation of Concerns
5. Deterministic Execution

---

## Summary

The Kernel Services Layer is:

a structured dependency system ensuring safe, testable, and deterministic execution of all kernel-level operations.
