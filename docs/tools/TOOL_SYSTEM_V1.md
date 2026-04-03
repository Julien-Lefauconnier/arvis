# ARVIS — Tool System V1

## Overview

The Tool System is the execution layer of the Cognitive OS.

It enables:
- deterministic cognition (pipeline)
- controlled side-effects (runtime)
- observable execution (tool results)
- safe retry mechanisms

This system is fully compatible with:
- ZKCS (Zero-Knowledge Cognitive System)
- ARVIS principles (traceability, bounded execution, abstention)

---

## Architecture


Cognitive Pipeline (pure)
↓
ActionDecision (tool selected)
↓
Cognitive Runtime
↓
ToolExecutor
↓
Tool (BaseTool)
↓
ToolResult → ctx.extra
↓
IR / State / Replay



---

## Key Principles

### 1. Separation of Concerns

| Layer | Responsibility |
|------|--------|
| Pipeline | Decision (pure, deterministic) |
| Runtime | Execution (side effects allowed) |
| Tool | External capability |
| IR | Observability |

---

### 2. Determinism

- Pipeline must remain pure
- Tool execution MUST NOT influence decision logic in the same run
- All effects are externalized in `ctx.extra`

---

### 3. Observability

Every tool execution produces:

```python
ToolResult(
    tool_name: str
    success: bool
    output: Any
    error: Optional[str]
    latency_ms: Optional[float]
)
```

Stored in:

```python
ctx.extra["tool_results"]
```

---

### 4. Replay Compatibility

- Tool execution is NOT replayed
- Only ToolResults are persisted
- Replay uses recorded state, not side-effects

---

## Execution Flow

### Step 1 — Decision

Pipeline selects tool:

```python
ActionDecision(tool="my_tool", allowed=True)
```

---

### Step 2 — Runtime Execution

```python
runtime.execute(ctx)
```

Triggers:

```python
ToolExecutor.execute(result, ctx)
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
ctx.extra["tool_results"].append(ToolResult(...))
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
- execution retried in runtime

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

---

## Extensibility

Future-ready for:

- async tools
- distributed execution
- tool scheduling
- multi-agent orchestration

---

## Version

### Tool System V1

Stable baseline for:

- local execution
- deterministic replay
- observable cognition