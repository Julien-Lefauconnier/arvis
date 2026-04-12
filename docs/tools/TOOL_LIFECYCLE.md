# Tool Lifecycle — ARVIS

## Overview

Describes the full lifecycle of a tool execution within the Kernel Core and Syscall System.

---

## Lifecycle Steps

### 1. Decision Phase (Pipeline)

Tool is selected:

```python
ActionDecision(tool="my_tool")
```

---

### 2. Kernel Detection Phase

The Kernel Core detects executable intent:

```python
if intent.action.tool:

syscall_handler.handle(...)
```

Responsibilities:

- validate execution eligibility
- trigger syscall execution
- enforce post-decision boundary

---

### 3. Execution Phase

Tool receives:

```python
{
    "decision": ...,
    "context": ...,
    "tool_payload": ...
    "syscall_context": {...}  # optional runtime metadata
}
```

IMPORTANT:

- Tool is executed ONLY via syscall
- Tool is NOT aware of pipeline execution
- Tool operates outside cognition

---

### 4. Result Capture

Success:

```python
SyscallResult(success=True, result=...)
```

Failure:

```python
SyscallResult(success=False, error="...")
```

---

### 5. Storage

```python
ctx.extra["syscall_results"]
```

This is the Syscall Journal.

---

### 6. State Integration

- CognitiveState (projection)
- CognitiveIR.tools (runtime artifacts)

IMPORTANT:

- Results are observable
- Results MUST NOT influence decision semantics of the same run

---

### 7. Retry Phase (optional)

Triggered by:

```python
ctx.extra["retry_tool"] = True
```

IMPORTANT:

- Retry decision is made by the pipeline (ToolRetryStage)
- Execution is still performed via syscall

---

### 8. Replay

- Tool NOT re-executed
- Only results replayed

Replay uses syscall journal only.
No tool execution occurs during replay.

Replay relies on:

- deterministic pipeline execution
- recorded SyscallResults

---

## Execution Boundary

Tool execution is strictly post-pipeline.

The pipeline never executes tools.

All tool executions occur via syscalls triggered by the Kernel Core.

STRICT RULE:

No tool execution is allowed outside the syscall system.

---

## Lifecycle Diagram

```text
Decision
→ Kernel
→ Syscall (tool.execute)
→ Tool
→ SyscallResult
→ Journal
→ Pipeline Feedback (next run)
```

Clarification:

- "Kernel" = execution authority
- "Syscall" = execution mechanism
- "Tool" = external capability

---

## Failure Handling

Case	Behavior
Exception	captured
Timeout	treated as failure
Invalid tool	rejected

All failures are:

- captured as SyscallResult(success=False)
- recorded in journal
- exposed to next pipeline execution

---

## Retry Logic

- bounded retries
- payload reuse
- safe conditions only

Retry is governed by:

- pipeline logic (ToolRetryStage)
- NOT by syscall system

---

## Guarantees

- no silent failures
- full traceability
- deterministic cognition
- isolated execution

Additionally:

- strict separation between cognition and execution
- replay-safe execution model
- syscall-only side-effects

---

## Future Extensions

- async tools
- streaming tools
- tool chaining
- tool planning

All extensions MUST:

- remain syscall-mediated
- preserve determinism constraints
- preserve replay compatibility

---

## Version

Lifecycle V1