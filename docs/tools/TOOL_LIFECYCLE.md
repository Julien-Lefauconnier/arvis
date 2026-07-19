# Tool lifecycle — ARVIS

Status: lifecycle contract for `0.1.0a10`.

## Overview

A tool is an external capability selected by cognition and dispatched only after
ARVIS has authorized, durably acknowledged and activated the exact invocation.
The cognitive pipeline never executes a tool body.

## Lifecycle

### 1. Decision

The pipeline produces a finalized `ActionDecision` containing a tool name and
payload. This is a request for authorization, not an execution capability.

### 2. Frozen authorization material

`ToolAuthorizationService`:

1. extracts the decision;
2. creates one canonical `FrozenEffectPayload`;
3. validates tool existence and input schema;
4. resolves principal, tenant, risk and authentication provenance;
5. derives a deterministic idempotency key;
6. evaluates `ToolPolicy` and configured consent/egress gates;
7. creates an immutable authorization snapshot.

`ToolManager` owns the confirmation transaction and mints a registered
single-use capability in state `MINTED`. A refusal carries a typed immutable
denial snapshot and no executable capability.

### 3. Governed syscall admission

The runtime passes the exact `ToolAuthorizationOutcome` to:

```python
SyscallHandler.handle(Syscall(name="tool.execute", ...))
```

The handler copies and validates the strict outcome, verifies manager ownership
and enforces production identity requirements.

### 4. Intent outbox

Before dispatch, `IntentOutboxService` builds and commits the exact intent. A
qualified sink returns an `AuditReceipt` binding:

- intent commitment;
- complete run ID;
- causal ID;
- durable position;
- store fingerprint.

An invalid receipt, sink exception or reused durable position aborts the
transaction. No tool body runs.

### 5. Activation and dispatch

The receipt activates the exact capability. `EffectDispatcher` atomically
consumes it and executes the frozen invocation. The adapter receives the
idempotency key through `ToolInvocation`; legacy adapters receive it in the
runtime payload.

### 6. Effect classification

Every `ToolResult` carries one explicit boundary state:

```text
PRE_EFFECT_REFUSAL
EFFECT_NOT_STARTED
EFFECT_STARTED
EFFECT_COMPLETED
EFFECT_FAILED
EFFECT_STATE_UNKNOWN
```

A confirmation is released only when ARVIS proves the effect did not start.
Once started or uncertain, it is conservatively consumed.

### 7. Result journal

The syscall result is converted to an `ExecutionArtifact` and journaled against
the exact intent using the same run ID, causal ID and intent commitment. An
effect result that cannot be journaled marks the run audit-incomplete.

### 8. Retry

Retry remains runtime-governed. Every attempt returns through the same syscall
path, receives a fresh authorization capability and reuses the same deterministic
idempotency key for the same logical action.

### 9. Replay

Replay consumes recorded artifacts. It never reactivates a capability or
re-executes the external tool.

## Forbidden routes

The following public calls fail closed:

```python
ToolManager.run(...)
ToolManager.execute_authorized(...)
ToolManager.activate_authorized(...)
ToolExecutor.execute_invocation(...)
ToolExecutor.execute(...)
```

Unit tests may call a tool implementation directly. End-to-end effect tests must
use `SyscallHandler` or `CognitiveOS`.

## Concurrency boundary

Capability transitions and confirmation reservations are atomic in one process.
Registries are currently process-local. The supported production doctrine is one
ARVIS instance per request/turn; shared multi-worker execution requires a future
external transactional registry.
