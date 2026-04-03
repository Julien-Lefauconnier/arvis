# Tool Lifecycle — ARVIS

## Overview

Describes the full lifecycle of a tool execution.

---

## Lifecycle Steps

### 1. Decision Phase (Pipeline)

Tool is selected:

```python
ActionDecision(tool="my_tool")
```

---

### 2. Runtime Phase

Runtime detects tool:

```python
if action.tool:
    executor.execute(...)
```

---

### 3. Execution Phase

Tool receives:

```python
{
    "decision": ...,
    "context": ...,
    "tool_payload": ...
}
```

---

### 4. Result Capture

Success:

```python
ToolResult(success=True, output=...)
```

Failure:

```python
ToolResult(success=False, error="...")
```

---

### 5. Storage

```python
ctx.extra["tool_results"]
```

---

### 6. State Integration

- CognitiveState.tool_results
- IR.tools

---

### 7. Retry Phase (optional)

Triggered by:

```python
ctx.extra["retry_tool"] = True
```

---

### 8. Replay

- Tool NOT re-executed
- Only results replayed

---

## Lifecycle Diagram

Decision → Runtime → Tool → Result → State → IR → Replay

---

## Failure Handling

Case	Behavior
Exception	captured
Timeout	treated as failure
Invalid tool	rejected

---

## Retry Logic

- bounded retries
- payload reuse
- safe conditions only

---

## Guarantees

- no silent failures
- full traceability
- deterministic cognition
- isolated execution

---

## Future Extensions

- async tools
- streaming tools
- tool chaining
- tool planning

---

## Version

Lifecycle V1