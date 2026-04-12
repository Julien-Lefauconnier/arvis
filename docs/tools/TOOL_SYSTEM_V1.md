# ARVIS — Tool System V1 (Syscall-Aligned)

## Overview

The Tool System is the **syscall-backed execution layer** of the Cognitive OS.

It enables:
- deterministic cognition (pipeline)
- controlled side-effects (kernel + syscalls)
- observable execution (tool results)
- safe retry mechanisms

This system is fully compatible with:
- ZKCS (Zero-Knowledge Cognitive System)
- ARVIS principles (traceability, bounded execution, abstention)

This component belongs to:

- Specification Hierarchy Level 4 (Execution Model)

---

## Architecture

```text
Pipeline (pure cognition)
↓
ActionDecision (tool selected)
↓
Kernel Core
↓
SyscallHandler
↓
ToolExecutor
↓
Tool (BaseTool)
↓
SyscallResult → ctx.extra
↓
IR / State / Replay
```

Note:

Any projection to external signal systems (Kernel Adapter Layer)
occurs strictly after IR generation and is not part of the Tool System.

Constraint:

The Kernel Core MUST only execute syscalls after:

- Gate validation is complete
- decision is finalized

---

## Syscall Mediation (CRITICAL)

Tools are NEVER executed directly.

All tool executions MUST be mediated through the syscall system.

This guarantees:

- execution traceability
- replay safety
- strict separation from cognition

Pipeline → Intent → Kernel → Syscall → Tool

---

## Key Principles

### 1. Separation of Concerns

| Layer | Responsibility |
|------|--------|
| Pipeline | Decision (pure, deterministic) |
| Kernel Core | Execution control |
| Syscalls | Side-effect mediation |
| Tool | External capability |
| IR | Observability |


---

### 2. Determinism

- Pipeline must remain pure
- All effects are externalized in `ctx.extra`
- Tool execution MUST NOT influence decision logic in the same run

Tool execution MUST NOT:

- influence decision semantics
- modify Gate outcomes
- inject signals into the cognitive pipeline

Additionally:

- Tools MUST NOT be invoked from the pipeline
- Tools MUST only be executed via syscalls

---

### 3. Observability

Every tool execution produces:

```python
SyscallResult(
    tool_name: str
    success: bool
    output: Any
    error: Optional[str]
    latency_ms: Optional[float]
)
```

Stored in:

```python
ctx.extra["syscall_results"]
```

SyscallResults MUST be propagated to:

- CognitiveState (if applicable)
- CognitiveIR (as runtime artifacts)

SyscallResults MUST be:

- deterministic representations of execution
- not re-executed during replay

---

### 4. Replay Compatibility

- Tool execution is NOT replayed
- Only SyscallResults are persisted
- Replay uses recorded state, not side-effects

Replay MUST NOT:

- trigger tool execution
- depend on external systems

Replay MUST rely exclusively on:

- recorded SyscallResults
- deterministic IR

---

## Execution Flow

### Step 1 — Decision

Pipeline selects tool:

```python
ActionDecision(tool="my_tool", allowed=True)
```

---

### Step 2 — Kernel Execution

```python
kernel.execute(ctx)
```

Triggers:

```python
syscall_handler.handle(intent, ctx)
```

---

### Step 3 — Tool Execution

```python
tool.execute({
    "decision": decision,
    "context": ctx,
    "tool_payload": {...}
})
```

---

### Step 4 — Result Storage

```python
ctx.extra["syscall_results"].append(SyscallResult(...))
```

---

### Step 5 — State + IR propagation

- CognitiveState
- CognitiveIR
- Replay

---

## Retry System

Retry is controlled via:

```python
ctx.extra["retry_tool"] = True
```

### Behavior

- previous tool is re-injected
- payload reused
- execution retried via syscall

---

### Retry Conditions (default)

- failure detected
- risk < threshold
- retry count < limit

---

## Safety Guarantees

- No tool execution in pipeline
- Retry bounded
- Side-effects isolated
- Failures captured (never silent)
- Kernel MUST NOT alter IR semantics

Additionally:

- Syscalls are the ONLY entry point for side-effects
- Tool execution is strictly post-decision
- Execution is fully observable and replay-safe

---

## Extensibility

Future-ready for:

- async tools
- distributed execution
- tool scheduling
- multi-agent orchestration

---

## Version

### Tool System V1 (Syscall-Aligned)

Stable baseline for:

- local execution
- deterministic replay
- observable cognition
- kernel-mediated execution