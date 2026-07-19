
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
ToolAuthorizationService
↓
ToolManager (confirmation + MINTED capability)
↓
SyscallHandler
↓
IntentOutboxService (exact receipt)
↓
Capability activation
↓
EffectDispatcher → Tool (BaseTool)
↓
ExecutionArtifact / SyscallResult
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
- Effect intents and results are journaled outside cognitive decision material
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
tool.execute_invocation(invocation)
```

The exact authorized invocation exposes only:

```python
invocation.payload
invocation.effect_context
invocation.idempotency_key
```

The compatibility `execute(input_data)` adapter receives `tool_payload`,
`effect_context`, `idempotency_key` and `invocation`. It never receives the
pipeline `context`. Tools must not derive identity, target, credentials or
services from mutable runtime state.

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
  `execute_authorized()` are hard refusals;
- `ToolExecutor.claim_minting_authority()` and
  `ToolExecutor.execute_invocation()` are hard refusals;
- minting, activation, revocation and capability consumption are private
  composition operations owned by the effect-boundary controller claimed by
  exactly one `SyscallHandler`.

The extracted services are internal architecture boundaries, not public API.
Their ownership and transaction are specified in
`docs/architecture/EFFECT_PATH.md`.

The production chain is therefore always:

```text
authorize
→ tool.execute syscall
→ intent outbox receipt
→ capability activation
→ effect execution
→ result journal
```

Focused unit-test compositions live under `tests/support`, outside the
distributed `arvis` package. Hosts such as Veramem must use `CognitiveOS` or the
governed syscall composition, never repository test support.

## Sealed context and host services

`AuthorizedEffectContext` is immutable commitment material, not a dependency
container. It carries principal, tenant, authentication provenance,
service/session identifiers, process/run identity and an optional host binding
commitment. It carries no credentials, database session, HTTP request, client,
pool, callback or logger.

Production hosts inject business services at tool construction. For example,
Veramem owns the document repository and constructs a tool with that service;
the tool combines the injected service with the frozen payload and sealed
identity. ARVIS owns authorization, capability, outbox and proof mechanics but
does not own Veramem's authentication, PostgreSQL transactions or distributed
worker coordination.
