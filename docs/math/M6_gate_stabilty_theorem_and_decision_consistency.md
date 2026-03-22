Markdown# M6 — Gate Stability Theorem & Decision Consistency

## 1. Objective

This document formalizes the decision layer stability mechanism implemented in the **ARVIS GateStage**.

It establishes:

- how Lyapunov-based signals are used to produce decisions,
- how adaptive stability modifies decisions,
- how global and switching constraints enforce safety,
- under which conditions the gate preserves stability guarantees.

This document extends:

- the hybrid system defined in M0–M1,
- the theorem chain T1–T5,
- the implementation-aligned proof skeleton M2,
- the adaptive runtime layer M4–M5.

---

## 2. Gate as a Decision Operator

We define the **Gate operator**:

$$
G : (x_t, z_t, q_t, W_t, \kappa^t, H_t) \mapsto v_t
$$

where:

- $W_t$ = composite Lyapunov energy,
- $\kappa^t$ = adaptive contraction estimate,
- $H_t$ = history (e.g. $\Delta W$ trajectory),
- $v_t \in \{ \text{ALLOW}, \text{CONFIRM}, \text{ABSTAIN} \}$.

---

## 3. Decision Structure (Code → Math Mapping)

The implemented `GateStage` corresponds to the following layered decisions:

### 3.1 Local Lyapunov Decision

$$
v_t^{(\text{local})} =
\begin{cases}
\text{ABSTAIN} & \text{if } \Delta W_t > \delta_{\text{strict}} \\
\text{CONFIRM} & \text{if } \Delta W_t > \delta_{\text{monitor}} \\
\text{ALLOW}    & \text{if } \Delta W_t \leq 0
\end{cases}
$$

### 3.2 Adaptive Override (M5)

Using the adaptive instability score:

$$
S_t = \tau_d \log J + \log(1 - \kappa^t)
$$

$$
v_t^{(\text{adaptive})} =
\begin{cases}
\text{ABSTAIN} & \text{if } S_t > 0 \\
\text{CONFIRM} & \text{if } S_t \approx 0 \\
v_t^{(\text{local})} & \text{otherwise}
\end{cases}
$$

### 3.3 Global Stability Enforcement

Using history $H_t = \{\Delta W_k\}_{k \leq t}$:

$$
v_t^{(\text{global})} =
\begin{cases}
\text{ABSTAIN} & \text{if instability detected in } H_t \\
v_t^{(\text{adaptive})} & \text{otherwise}
\end{cases}
$$

### 3.4 Switching Constraint

$$
v_t^{(\text{switch})} =
\begin{cases}
\text{ABSTAIN} & \text{if switching condition violated} \\
v_t^{(\text{global})} & \text{otherwise}
\end{cases}
$$

### 3.5 Final Fusion Operator

The implemented fusion is:

$$
v_t = F\bigl( v_t^{(\text{local})}, v_t^{(\text{adaptive})}, v_t^{(\text{global})}, v_t^{(\text{switch})} \bigr)
$$

with **monotonic safety ordering**:

### 3.6 Hard Kappa Invariant (Final Enforcement)

The implementation enforces a **post-fusion hard invariant**:

$$
\kappa\text{-violation} \;\Rightarrow\; v_t = \text{ABSTAIN}
$$

This constraint is applied **after fusion and policy layers** and cannot be overridden.

It ensures that:

- contraction failure dominates all other signals,
- no recovery or fusion logic can re-enable unsafe evolution,
- the Gate remains a **strict safety operator**.

This corresponds in code to:

```python
if metrics.kappa_violation:
    verdict = ABSTAIN
```

$$
\text{ABSTAIN} \succ \text{CONFIRM} \succ \text{ALLOW}
$$

---

## 4. Main Theorem — Gate Stability Preservation

**Theorem T6 — Gate Stability Preservation**

**Under assumptions:**

- A1–A15 (M1)
- projection validity on $\mathcal{O}_{\text{valid}}$ (M3)
- adaptive estimator bounded (M4)
- fusion operator is monotone
- ABSTAIN prevents state update
- CONFIRM introduces bounded additional delay

**then:**

The Gate operator $G$ preserves practical stability of the ARVIS system on the validated domain.

**Formal statement:**

For all trajectories $o_t \in \mathcal{O}_{\text{valid}}$:

$$
W(t+1) \leq C e^{-\beta t} W(0) + \gamma \sup_{k \leq t} \|w_k\|^2
$$

provided that:

$$
v_t \neq \text{ALLOW} \quad \Rightarrow \quad \text{system evolution is slowed or blocked}
$$

---

## 5. Interpretation

Le **Gate** devient un **filtre de stabilité dynamique**. Il garantit que :

- les trajectoires instables **ne passent pas**,
- les trajectoires marginales **sont ralenties**,
- les trajectoires stables **passent**.

---

## 6. Critical Property — Monotonic Safety

The Gate must satisfy:

$$
v_t^{(1)} \preceq v_t^{(2)} \quad \Rightarrow \quad \text{risk}(v_t^{(1)}) \leq \text{risk}(v_t^{(2)})
$$

This is enforced in code by the strict ordering:

$$
\text{ABSTAIN} > \text{CONFIRM} > \text{ALLOW}
$$

---

## 7. Connection with Implementation

`gate_stage.py` implements exactly:

- $\Delta W$ → `delta_w`
- $W_t$ → `w_current`
- adaptive margin → `adaptive_metrics["margin"]`
- switching → `switching_condition`
- global → `GlobalStabilityGuard`
- fusion → `multiaxial_fusion`

and stores in

```python
ctx.extra["theoretical_trace"]
```

Additionally, the implementation exposes:

- `kappa_violation`, `kappa_gap`
- `kappa_margin`, `kappa_band`
- `validity_envelope`

which bridge theoretical conditions to runtime observability.