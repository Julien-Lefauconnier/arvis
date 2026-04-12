# ARVIS Specification Hierarchy v1

## Status

* Version: v1
* Scope: Normative (Meta-Specification)
* Component: ARVIS Standard Governance Layer

---

## 1. Purpose

This document defines the **hierarchy, precedence, and interaction rules** between all ARVIS normative specifications.

It establishes:

* which documents are **authoritative**
* how conflicts must be resolved
* how the standard is structured as a whole

This file is the **entry point for understanding ARVIS as a standard system**.

---

## 2. Normative Hierarchy (Highest → Lowest)

The ARVIS specification is organized into the following priority levels:

### Level 1 — System Invariants (ABSOLUTE AUTHORITY)

* `ARCHITECTURE_INVARIANTS.md`

These define **non-negotiable system constraints**.

Rules:

* MUST always hold
* CANNOT be overridden
* Violation invalidates the system

---

### Level 2 — Core Decision Authority

* `ARVIS_GATE_SPEC_V1.md`

Defines:

* the canonical verdict model
* constraint enforcement
* decision admissibility

Rules:

* Gate verdict is the **the primary authority on decision admissibility**, but may be extended by post-gate layers such as confirmation and execution policies.
* All upstream components MUST comply with Gate constraints

---

### Level 3 — External Contract (IR Layer)

* `ARVIS_IR_SPEC_V1.md`
* `ARVIS_PUBLIC_OBJECT.md`
* `ARVIS_REASON_CODE_REGISTRY.md`

Defines:

* canonical representation (`CognitiveIR`)
* public objects and schemas
* reason code semantics

Rules:

* MUST be deterministic
* MUST reflect Gate output exactly
* MUST be stable across executions
* IR defines the canonical boundary of cognition.
* All downstream layers MUST derive strictly from IR without modifying its semantics.

---

### Level 4 — Response Construction Layer

* `CONVERSATION_SPEC_V1.md`
* `LINGUISTIC_SPEC_V1.md`

Defines:
- transformation of validated cognition into response strategies
- response planning and linguistic realization constraints

Rules:
- MUST NOT modify decision semantics
- MUST derive strictly from IR
- MUST preserve determinism and safety constraints
- MUST NOT introduce new decision logic

---

### Level 5 — Execution Model

* `PIPELINE.md`
* `KERNEL_CORE.md`
* `SYSCALL_SPEC.md`
* `TOOL_SYSTEM_V1.md` (derived layer)


Defines:

* deterministic cognitive execution (pipeline)
* kernel-driven execution control (processes, scheduler, interrupts)
* syscall-based side-effect execution
* runtime orchestration (tick-based execution model)

Rules:

* pipeline MUST remain pure and deterministic
* kernel MUST NOT modify cognitive semantics
* all side-effects MUST be executed via syscalls
* syscall results MUST be the canonical execution artifacts
* execution MUST be replay-safe (no side-effect re-execution)

---

### Syscall Authority Principle (CRITICAL)

All execution of side-effects MUST be performed through syscalls.

Rules:

- Syscalls are the ONLY authorized mechanism for external interactions
- Tool execution is a specialization of syscalls
- No execution MUST occur outside the syscall layer
- SyscallResults MUST be the canonical representation of execution

This ensures:

- deterministic cognition
- isolated execution
- replay-safe behavior

---

### Level 6 — Constraint Input Layer

* `ARVIS_PROJECTION_SPEC_V1.md`
* `ARVIS_VALIDITY_ENVELOPE_SPEC_V1.md`

Defines:
- projection certification
- validity constraints

Rules:
- MUST feed structured inputs into Gate
- MUST be consistent with Gate evaluation inputs
- MUST remain deterministic and auditable
- MUST NOT override Gate semantics
- Projection invalid ⇒ Validity invalid
- Validity MUST be evaluated before or during Gate evaluation

IMPORTANT:

These layers operate strictly within cognition.
They MUST NOT depend on runtime execution or syscalls.

---

### Level 7 — Interoperability / Canonical Projection Layer

* `KERNEL_ADAPTER.md`

Defines:

* mapping from ARVIS IR → external canonical signal systems
* deterministic projection rules
* canonical signal emission constraints

This layer includes:

- Kernel Adapter
- Rule Engine (projection only)
- Canonical Signal Factory

Rules:

* MUST be semantically deterministic (excluding runtime metadata)
* MUST NOT introduce decision logic
* MUST NOT override or reinterpret Gate outputs
* MUST NOT influence the cognitive pipeline
* MUST operate strictly post-IR
* MUST comply with external canonical registries (closed-world assumption)

IMPORTANT:

This layer is NOT part of:

- cognition
- decision-making
- execution logic

It is a **pure projection layer** between:

> ARVIS internal semantics (IR)
> and external canonical systems (e.g. Veramem Kernel)

It ensures:

- interoperability
- canonical consistency
- external validation compatibility

It MUST NOT:

- resolve conflicts
- prioritize signals
- apply business logic
- introduce side effects

---

#### Tool System Position

The Tool System is a specialization layer within the Syscall System.

It is responsible for:

- exposing tool-based syscalls
- mapping tool abstractions to syscalls
- providing structured execution interfaces

The Tool System operates strictly in the Runtime layer and MUST NOT:

- influence decision semantics
- bypass syscall execution

Tool execution is:

- observable through SyscallResults
- replay-safe (results only)
- fully contained within the syscall layer

---

### Level 8 — Compliance & Verification

* `ARVIS_COMPLIANCE_SUITE_V1.md`

Defines:

* conformance requirements
* validation procedures
* reproducibility expectations

Rules:

* MUST validate all higher-level specifications
* MUST NOT redefine system semantics

---

### Level 9 — Architecture & Informative Documents

* `ARCHITECTURE.md`
* `OVERVIEW.md`
* `WHY_ARVIS.md`
* `ARVIS_VS_LLM.md`
* `REFLEXIVE.md`
* `COGNITIVE_STATE.md`
* `IR.md` (non-normative overview)

These documents are **informative**.

Rules:

* DO NOT define normative behavior
* MUST NOT contradict higher-level specifications
* MAY explain, illustrate, or contextualize the system

NOTE:
Reflexive is not a standalone system layer.
It is a read-only projection of Level 3 public objects:
- CognitiveState
- DecisionTrace
- CognitiveIR
- Timeline

---

## 3. Conflict Resolution Rules

In case of conflict between documents:

1. **Higher-level specification always prevails**
2. System invariants override all other rules
3. Gate specification overrides pipeline behavior
4. IR specification overrides serialization or representation differences
5. Canonical Projection Layer MUST NOT override IR semantics
6. Informative documents MUST be ignored in conflicts
7. IR MUST be considered the canonical boundary before response construction. 
    Conversation and linguistic layers MUST NOT override IR semantics.
8. Syscall Specification overrides all execution-related behavior
   - No execution mechanism may bypass syscalls
   - No alternative execution representation is allowed

---

## 4. Normative vs Implementation-Aligned Specifications

Each specification MUST declare its nature:

* **Normative** → defines required behavior
* **Implementation-aligned** → reflects current implementation but not mandatory

Rules:

* Normative specifications are binding
* Implementation-aligned sections MUST NOT restrict alternative compliant implementations

---

## 5. Stability of the Standard

### 5.1 Versioning

Each specification MUST:

* declare its version
* define compatibility expectations

---

### 5.2 Backward Compatibility

* Public objects (IR, Gate, Reason Codes) MUST remain backward compatible within a major version
* Breaking changes REQUIRE version increment

---

### 5.3 Forward Compatibility

* Unknown fields in IR MUST be safely ignored
* Extensions MUST NOT break determinism

---

## 6. Compliance Requirement

An implementation is **ARVIS-compliant** if and only if:

* all Level 1 invariants are respected
* Gate behavior matches the Gate specification
* IR output matches the IR specification
* execution is deterministic
* compliance suite tests pass

If a Canonical Projection Layer is implemented:

* it MUST preserve IR semantics exactly
* it MUST remain deterministic
* it MUST NOT introduce decision or policy logic
* it MUST comply with external canonical registry constraints

---

## 7. Design Principle

The hierarchy enforces the core ARVIS principle:

> Execution is flexible,
> but validity is constrained.

* The pipeline MAY evolve
* The IR MAY extend
* The system MAY adapt

But:

* invariants MUST hold
* Gate MUST remain authoritative
* IR MUST remain canonical

---

## 8. Summary

| Level | Role                          | Authority          |
| ----- | ----------------------------- | ------------------ |
| 1     | Invariants                    | Absolute           |
| 2     | Gate                          | Decision authority |
| 3     | IR / Public Objects           | External contract  |
| 4     | Conversation / Linguistic     | Response layer     |
| 5     | Pipeline + Kernel + Syscalls  | Execution model    |
| 6     | Projection / Validity         | Constraint inputs  |
| 7     | Canonical Projection          | Interoperability   |
| 8     | Compliance                    | Verification       |
| 9     | Architecture / Docs           | Informative        |

---

## 9. Final Statement

ARVIS is defined as a **hierarchically constrained cognitive system**.

No component is valid in isolation.

The system is only compliant if **all layers respect this hierarchy**.
