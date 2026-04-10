# MEMORY SYSTEM SPEC (v1 — Normative)

## 1. Purpose

The Memory System defines how long-term information is:

- stored
- constrained
- projected into cognition
- exposed for audit

It enables:

- contextual continuity
- constraint enforcement
- auditability of memory influence

---

## 2. Architectural Role

```text
Memory
→ (projection)
→ Cognitive Pipeline (Bundle Stage)
→ Decision

AND

Memory
→ (projection)
→ Conversation Layer

AND

Memory
→ (audit projection)
→ Public Objects
```

IMPORTANT:

Memory interactions MUST be consistent with CognitiveContextIR.
Memory MUST NOT bypass IR as the canonical boundary of cognition.

---

## 3. Core Principle

    Memory influences cognition, but does not decide.

Memory MUST:

- NOT introduce new decision semantics
- remain fully deterministic given identical inputs and policy

---

## 4. Components

### 4.1 MemoryLongRegistry

```text
memory_long_registry.py
```

- authoritative memory store
- structured entries

---

### 4.2 MemoryLongEntry

Represents a unit of memory.

Contains:

- content
- constraints
- metadata
- timestamps

Constraints:

- content MUST be structured and deterministic
- content MUST NOT contain executable or dynamic logic
- entry MUST be immutable once created

---

### 4.3 MemoryLongPolicyGate

Controls:

- what memory can be used
- under which conditions

Responsibilities:

- enforce access constraints
- enforce security and visibility rules
- ensure deterministic filtering

---

### 4.4 MemoryLongProjector

Projects memory into:

- cognitive context
- conversation context

Constraints:

- MUST NOT introduce new information beyond MemoryLongEntry
- MUST preserve semantic integrity
- MUST be deterministic

--- 

### 4.5 MemoryLongSnapshot

Represents a deterministic projection of memory at execution time

---

## 5. Memory Flow

### Step 1 — Retrieval

```text
MemoryLongRegistry → entries
```

---

### Step 2 — Policy Filtering

```text
entries → MemoryLongPolicyGate → filtered entries
```

---

### Step 3 — Projection

```text
filtered entries → MemoryLongProjector → signals
```

Injected into:

- ctx.long_memory
- CognitiveContextIR

Constraints:

- projection MUST be deterministic
- projection MUST NOT alter decision semantics
- projection MUST be traceable via MemoryLongSnapshot

---

### Step 4 — Snapshot (Audit)

```text
filtered entries → MemoryLongSnapshot
```

MemoryLongSnapshot MUST:

- be deterministic
- fully represent memory used in execution
- be consistent with CognitiveContextIR

---

## 6. Memory Integration Points

### 6.1 Cognitive Pipeline

- Bundle Stage
- Passive Context Stage

Constraints:

- memory MUST be injected before decision computation
- memory MUST NOT be modified during pipeline execution

### 6.2 Conversation Layer

- response shaping
- constraint enforcement

Constraints:

- memory MUST NOT introduce new decision semantics
- memory MUST only constrain communication

---

## 7. Memory Snapshot (Public Representation)

Memory MUST be exposed as a snapshot, not raw storage.

Snapshot MUST:

- be deterministic
- be auditable
- represent only policy-approved memory

---

## 8. Invariants

- Memory MUST be deterministic per execution
- Memory MUST NOT mutate during pipeline execution
- Memory MUST be filtered before use
- Memory MUST NOT introduce hidden reasoning
- Memory MUST NOT override Gate decisions
- Memory MUST NOT introduce new semantic content
- Memory MUST be fully traceable via MemoryLongSnapshot

---

## 9. Security Model

Memory exposure MUST respect:

- policy filtering
- redaction rules
- constraint visibility
- strict access control
- deterministic exposure rules

---

## 10. Separation from IR

Memory is partially represented in:

- CognitiveContextIR (constraints, preferences)

BUT:

    Full memory is NOT embedded in IR

Instead:

- IR → cognitive usage
- MemorySnapshot → audit exposure

Constraints:

- IR MUST reflect memory influence, not memory content
- MemorySnapshot is the ONLY authoritative audit view of memory