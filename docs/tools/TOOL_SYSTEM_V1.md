
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

## Governance and Capability Manifest

Every tool carries a `ToolSpec` whose fields govern its execution. The
`ToolPolicyEvaluator` enforces the risk ceiling (`max_risk`) and the
confirmation requirement (`requires_confirmation`) before a syscall runs; the
`tool.execute` syscall journals an `ExecutionArtifact` unconditionally, so
`audit_required` is a declarative flag rather than a journaling gate.

The spec also carries a **capability manifest**: declarative metadata describing
where a tool's data goes and what gates it, so a host can govern sovereignty,
egress and consent uniformly across local and external (e.g. MCP) tools.

| Field | Meaning |
|-------|---------|
| `provider` | Third-party service identity, or `None` for a local tool. |
| `data_egress` | Whether the tool sends the caller's data outbound. |
| `data_class` | Host-defined sensitivity of the data handled. |
| `required_consent` | Opaque consent key the host must have granted. |
| `reversible` | Whether the effect can be undone. |

The derived `crosses_trust_boundary` property (`provider is not None`) separates
sovereign tools from connected ones. ARVIS does not interpret the opaque labels
(`provider`, `data_class`, `required_consent`); a host maps them onto its consent
system, data taxonomy and egress policy. Because governance is read from the
manifest rather than hard-coded per tool, adding a new local or external tool is
a declaration, not a policy change.

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

---

## Effect execution boundary

Tool registration and tool execution are deliberately separate surfaces.
`ToolManager` and `ToolExecutor` may be imported by a host for composition, but
neither object exposes a public route that can trigger an effect:

- `ToolManager.run()` is a hard refusal;
- `ToolManager.activate_authorized()`, `abort_authorized()` and
  `execute_authorized()` require the private effect-boundary permit claimed by
  exactly one `SyscallHandler`;
- `ToolExecutor.claim_minting_authority()` and
  `ToolExecutor.execute_invocation()` are hard refusals;
- minting and capability consumption are internal composition operations.

The production chain is therefore always:

```text
authorize
→ tool.execute syscall
→ intent outbox receipt
→ capability activation
→ effect execution
→ result journal
```

Tests inside the ARVIS repository may use private helpers whose names explicitly
contain `for_tests`. They are not API, are not exported, and must never be used
by hosts such as VeraMem.
