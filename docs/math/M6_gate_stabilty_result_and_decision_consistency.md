# ARVIS — M6: Gate Stability Filtering & Decision Consistency (v2 — Implementation-Aligned)

## Objective
This document defines the role of the **Gate operator** in ARVIS.

The Gate **does not generate dynamics**.  
It acts as a **multi-layer filtering operator** on admissible system evolution, based on:

- Lyapunov stability signals
- adaptive runtime estimation
- switching constraints
- projection validity
- runtime validity diagnostics

This document is **critical** for safety:
> It acts as the final safety filter before any transition is executed in the real system.

---

## 1. Gate as a Decision Filter

We define the Gate operator as:

$$
G:(W_t, \Delta W_t, \kappa^t, P_t, V_t, H_t) \mapsto v_t
$$

where:

$$
v_t \in \{\text{ALLOW}, \text{REQUIRE CONFIRMATION}, \text{ABSTAIN}\}
$$

- $V_t$ : runtime validity envelope  
- $P_t$ : projection certificate  
- $H_t$ : historical / contextual signals  

**Important**: The Gate does not modify the state directly. It only constrains which transitions are allowed.

---

## 2. Decision Structure
The Gate decision is produced through a **multi-stage filtering pipeline**:

1. Kernel evaluation (Lyapunov + switching + adaptive signals)
2. Fusion layer (multi-signal aggregation)
3. Policy enforcement
4. Validity enforcement
5. Projection enforcement
6. Hard safety vetoes

Each stage may restrict or override previous decisions.

---

## 3. Gate Semantics (CRUCIAL)
Each decision corresponds to a precise constraint on system evolution:

- **ALLOW** → no restriction  
- **REQUIRE CONFIRMATION** → constrained / delayed evolution  
- **ABSTAIN** → transition is blocked or replaced  

The Gate enforces the following **safety ordering**:

$$
\text{ABSTAIN} \succ \text{REQUIRE CONFIRMATION} \succ \text{ALLOW}
$$

---

## 4. Main Result — Extended Conditional Filtering Property

**Result T6 — Gate Stability Filtering (Extended)**

Under assumptions A1–A15 (M1), and assuming:
- the underlying system satisfies T1 (stability condition)
- the runtime projection certificate $P_t$ remains valid (i.e. $P_t.\text{domain\_valid} = \text{True}$)
- the Gate enforces the constraints (C1)–(C6) below

Then the Gate prevents execution of locally destabilizing or invalid transitions.

### Constraints Enforced by the Gate

**(C1) Lyapunov constraint**  
$$
\Delta W_t > 0 \quad \Rightarrow \quad v_t \neq \text{ALLOW}
$$

**(C2) Projection validity constraint**  
$$
P_t.\text{domain\_valid} = \text{False} \quad \Rightarrow \quad v_t = \text{ABSTAIN}
$$

**(C3) Projection boundary constraint**  
$$
\text{margin}(P_t) < \epsilon \quad \Rightarrow \quad v_t \neq \text{ALLOW}
$$

**(C4) Adaptive instability constraint**  
$$
\kappa^t \leq 0 \quad \Rightarrow \quad v_t = \text{ABSTAIN}
$$

**(C5) Switching stability constraint**  
switching violation $\quad \Rightarrow \quad v_t \neq \text{ALLOW}$

**(C6) Exponential bound constraint**  
$$
\frac{W_{t+1}}{W_t} > \text{threshold} \quad \Rightarrow \quad v_t \neq \text{ALLOW}
$$

---

## 5. Projection-Aware Safety Layer (NEW)

The Gate integrates a projection safety layer based on the runtime certificate:

$$
$P_t = (\text{domain\_valid}, \text{margin}, \text{is\_projection\_safe})
$$

This layer enforces:

- **Hard invalidity block**  
  $\text{domain\_valid} = \text{False} \implies \text{ABSTAIN}$

- **Boundary protection**  
  $0 \leq \text{margin} < \epsilon \quad \Rightarrow \quad \text{REQUIRE CONFIRMATION}$

- **Coupled instability rejection**  
  $\neg P_t.\text{is\_projection\_safe} \land (\Delta W_t > 0 \lor \text{global unsafe}) \quad \Rightarrow \quad \text{ABSTAIN}$

**Interpretation**:  
The Gate is not only stability-aware — it is also **projection-aware**.

---

## 6. Adaptive Layer

The adaptive score used as runtime stability indicator is:

$$
S_t = \tau_d \log J + \log(1 - \kappa^t)
$$

The adaptive estimator is noisy, local, and **not certified**. Nevertheless, the Gate enforces:

- **Adaptive hard veto**: $\kappa^t \leq 0 \implies \text{ABSTAIN}$
- **Adaptive margin zones**:
  - stable zone → no restriction
  - warning zone → REQUIRE CONFIRMATION
  - critical zone → downgrade ALLOW
  - unstable zone → ABSTAIN

---

## 7. Validity Envelope Integration

The Gate consumes the runtime diagnostic object:

$$
V_t = \text{ValidityEnvelope}
$$

If:

$$
V_t.\text{valid} = \text{False}
$$

then:

$$
v_t \neq \text{ALLOW}
$$

> The validity envelope is **not** a mathematical invariant nor a proof object.  
> It is a runtime safety aggregation layer.

---

## 8. Kappa Invariant

The hard invariant:

$$
\text{kappa violation} \quad \Rightarrow \quad \text{ABSTAIN}
$$

ensures that no transition is accepted when contraction is violated.

This is a **design constraint**, not a theorem.

---

## 9. Monotonic Safety Property

The Gate fusion operator satisfies:

$$
\text{ABSTAIN} \succ \text{REQUIRE CONFIRMATION} \succ \text{ALLOW}
$$

This guarantees that more restrictive decisions always dominate less restrictive ones.

---

## 10. Relation to Global Stability

If:
- the base system is stable (T1 holds)
- the runtime projection certificate remains valid ($P_t.\text{domain\_valid} = \text{True}$)
- the Gate enforces constraints (C1)–(C6)

then the combined system preserves **practical stability with high probability**.

---

## 11. Interpretation

The Gate does not guarantee stability by itself.  

Instead, it acts as a **multi-layer safety filter** combining:

- Lyapunov filtering
- adaptive detection
- projection validation
- runtime diagnostics

---

## 12. Limitations

The Gate does **not**:
- guarantee global stability
- ensure correctness of the projection $\Pi$
- validate assumptions A1–A15
- provide formal certification
- eliminate all instability (only reduces its probability)

---

## 13. Summary

The Gate is:
- a stability-aware decision filter
- a projection-aware safety layer
- a multi-signal enforcement mechanism
- a runtime protection system, **not** a proof system

---

## 14. Guiding Principle
> Stability guarantees are only as strong as the weakest safety filter.

---

## 15. Next Step
→ Implementation & extensive simulation testing  
→ Integration with runtime monitoring  
→ Empirical validation of false-positive / false-negative rates