# ARVIS MEMORY SPECIFICATION V1
## Kernel Memory Subsystem — ARVIS-MEM-01

**Version:** 1.0  
**Status:** Stable (implementation-aligned)  
**Scope:** Kernel Core  
**Applies to:** `arvis/kernel_core/memory/*`  

---

## 1. Overview

The ARVIS Memory Subsystem defines a **deterministic, policy-controlled, kernel-managed memory layer**.

It provides:

- controlled long-term memory storage,
- policy-filtered retrieval,
- deterministic snapshot construction,
- syscall-based access,
- replay-safe execution semantics.

It also provides:

- execution-safe projection into the cognitive pipeline,
- IR-safe memory influence exposure,
- syscall journal metadata for auditability,
- strict separation between stored memory, projected memory, and public memory signals.

Memory is a **first-class kernel subsystem**, equivalent in architectural status to:

- VFS (structured namespace),
- Syscalls (execution boundary),
- Process runtime.

---

## 2. Design Principles

### 2.1 Determinism

Memory operations MUST be deterministic:

- identical repository state → identical results,
- ordering MUST be stable and explicitly defined,
- snapshot construction MUST be reproducible.

---

### 2.2 Policy-first access

All memory access MUST pass through a **policy filter**:

```text
Repository → Policy → Projection → Snapshot
```

No raw repository access is allowed outside the memory service.

---

### ZKCS compliance

The memory subsystem MUST:

- not perform hidden inference,
- not derive semantic meaning implicitly,
- expose only explicit stored data,
- preserve traceability of memory influence.

The subsystem MAY project safe derived indicators, but only when those indicators are:
- deterministic,
- schema-bounded,
- non-semantic,
- non-reconstructive of raw memory contents.

---

### 2.4 Snapshot immutability

During a pipeline execution:

- memory is consumed as a snapshot,
- no in-flight mutation is allowed,
- all writes happen via syscalls outside execution flow.

---

### 2.5 Kernel boundary enforcement

Memory access MUST occur exclusively through:

- MemoryService
- KernelServiceRegistry
- memory syscalls

Direct repository access is forbidden in kernel execution paths.

---

## 3. Architecture

### 3.1 Layered structure

```text
memory/
  ├── repository        (storage contract)
  ├── repositories      (implementations)
  ├── policy            (filtering rules)
  ├── projection        (execution view)
  ├── snapshot          (deterministic representation)
  ├── service           (orchestration)
  └── adapters          (integration with pipeline / IR / legacy long-memory bridge)
```

---

### 3.2 Data flow

```text
[Syscall]
    ↓
MemoryService
    ↓
Repository → Policy → Projection → Snapshot
    ↓
Structured deterministic result
    ↓
Syscall journal

[Pipeline]
    ↓
PassiveContext / Decision / Bundle integration
    ↓
Projected memory influence
    ↓
IR-safe context exposure
```

---

## 4. Domain Model

### 4.1 MemoryEntry

Represents a single memory record.

#### Fields
- key: str
- memory_type: str
- value_ref: Optional[str]
- notes: Optional[str]
- source: str
- created_at: datetime
- expires_at: Optional[datetime]
- revoked_at: Optional[datetime]

---

### 4.2 MemorySnapshot

Represents the deterministic view of memory.

#### Fields
- active_entries: list[MemoryEntry]
- total_entries: int
- revoked_entries: int
- last_updated_at: Optional[datetime]
- created_at: datetime

---

## 5. Repository Contract

### 5.1 Responsibilities

The repository:

- stores memory entries,
- does NOT apply policy,
- does NOT perform projection,
- does NOT enforce visibility.

---

### 5.2 Required methods

- list_entries(user_id)
- list_active_entries(user_id)
- list_active_entries_batch(user_ids)
- get_entry(user_id, key)
- add_entry(...)
- replace_entry(...)
- revoke_entry(...)

---

### 5.3 Deterministic ordering

All returned collections MUST be ordered by:

- created_at
- key
- memory_type

---

## 6. Policy Layer

- 6.1 Responsibilities

The policy layer filters entries based on:

- revocation status,
- expiration,
- allowed memory types,
- visibility rules.

---

### 6.2 Minimum rules (V1)

- exclude revoked entries,
- exclude expired entries,
- include only supported types.

---

### 6.3 Extensibility

Future policy layers MAY include:

- capability checks,
- per-domain restrictions,
- contextual access filtering.

---

## 7. Projection Layer

### 7.1 Purpose

Transforms filtered entries into a usable execution representation.

---

### 7.2 Constraints

Projection MUST:

- be deterministic,
- preserve traceability,
- not infer hidden semantics.

---

## 8. Snapshot Builder

### 8.1 Purpose

Builds the canonical memory snapshot.

---

### 8.2 Requirements

- deterministic construction,
- consistent metadata,
- stable ordering,
- no hidden transformation.

---

## 9. Memory Service

### 9.1 Role

The MemoryService orchestrates:

- repository access,
- policy filtering,
- projection,
- snapshot construction.

---

### 9.2 Responsibilities

- provide read operations:
- list
- get
- snapshot
- provide mutation operations:
- write
- revoke
- enforce policy
- guarantee determinism

---

## 10. Kernel Service Registry Integration

The memory subsystem is exposed via:

```python
KernelServiceRegistry.memory_service
```

---

### 10.1 Rules

- syscalls MUST use registry access,
- no direct instantiation,
- missing service MUST degrade gracefully.

---

## 11. Syscall Interface

### 11.1 Supported syscalls

#### Read
- memory.list
- memory.get
- memory.snapshot

#### Mutation
- memory.write
- memory.revoke

---

### 11.2 Result format

All results MUST be:

- structured,
- deterministic,
- JSON-serializable.

---

### 11.3 Error model

Standard error codes:

- memory_entry_not_found
- memory_entry_revoked
- memory_entry_expired
- memory_policy_denied
- memory_invalid_key
- memory_conflict
- no_memory_service

---

## 12. Replay Semantics

### 12.1 Policy

All memory syscalls use:

```text
journal_only_replay
```

---

### 12.2 Rationale

Memory is time-dependent. Recomputing would:

- break determinism,
- invalidate auditability.

---

## 13. Pipeline Integration

### 13.1 Context injection

Memory snapshot is injected into:

```text
CognitivePipelineContext.long_memory_snapshot
```

---

### 13.2 Constraints

- snapshot is read-only,
- no stage may mutate memory,
- memory influences decision but does not redefine logic.

---

## 14. IR Integration

### 14.1 Exposure

IR MUST expose:

- constraints
- preferences

NOT raw memory content.

---

### 14.2 Example

```json
{
  "long_memory_constraints": ["no_share"],
  "long_memory_preferences": {
    "language": "fr"
  }
}
```

---

## 15. Invariants

The subsystem MUST guarantee:

- determinism,
- policy enforcement,
- snapshot immutability,
- syscall-only mutation,
- explicit error handling,
- replay safety.

---

## 16. Non-goals (V1)

The following are explicitly excluded:

- semantic search,
- ranking,
- probabilistic retrieval,
- distributed memory,
- encryption layers,
- capability system.

---

## 17. Future Extensions

Planned evolutions:

- capability-based access control,
- persistent storage backend,
- encrypted memory,
- VFS integration,
- conversation shaping,
- distributed synchronization.

---

## 18. Summary

The ARVIS Memory Subsystem V1 establishes:

- a deterministic memory kernel,
- a policy-controlled access layer,
- a syscall interface,
- a replay-safe execution model.

It transforms memory from a conceptual feature into a true kernel resource.