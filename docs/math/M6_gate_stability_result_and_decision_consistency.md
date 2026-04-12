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
G:(W_t, \Delta W_t, \kappa^t, P_t, V_t, H_t) \mapsto v_t^{\text{gate}}
$$

where:

$$
v_t^{\text{gate}} \in \{\text{ALLOW}, \text{REQUIRE CONFIRMATION}, \text{ABSTAIN}\}
$$

- $V_t$ : runtime validity envelope  
- $P_t$ : projection certificate  
- $H_t$ : historical / contextual signals


**Important**: The Gate does not modify the state directly. It only constrains which transitions are allowed.
The projection-control layer $\Pi_{\text{ctrl}}$ is applied **after** the core Gate decision and therefore does not belong to the input signature of $G$ itself.

---

## 2. Decision Structure
The Gate decision is produced through a **multi-stage filtering pipeline**:

1. Kernel evaluation (Lyapunov + switching + adaptive signals)
2. Fusion layer (multi-signal aggregation)
3. Policy enforcement
4. Validity enforcement
5. Projection enforcement
6. Hard safety vetoes

These stages produce the intermediate decision $v_t^{\text{gate}}$.

The final system decision is then obtained by composition with the projection-control layer:

$$
v_t^{\text{final}} = \min_{\succ}\big(v_t^{\text{gate}}, v_t^{\pi}\big)
$$

where:

$$
v_t^{\pi} = \Pi_{\text{ctrl}}(x_t,z_t,H_t)
$$

## 2.1 Decision Overrides (Implementation-Aligned)

The Gate decision may be modified by post-processing overrides:

1. Recovery override  
  - If recovery is detected and validity is satisfied, the system may promote a non-allow verdict to ALLOW.

2. Uncertain recovery  
  - If recovery is detected but validity is not guaranteed, the system must enforce REQUIRE_CONFIRMATION.

3. Validity enforcement  
  - Invalid validity does not necessarily force ABSTAIN but may enforce REQUIRE_CONFIRMATION depending on context.

4. Projection override (Π_ctrl)
  - A projection-based control layer may restrict the final decision based on structured projected state analysis.
  - This layer is conservative: it can only restrict the final decision (never relax it).

These overrides are implementation-aligned safety mechanisms and extend the theoretical constraints (C1–C6).

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

This ordering is strictly enforced across all core Gate layers and in the final composition with projection-based control.

---

## 4. Main Result — Extended Conditional Filtering Property

**Result T6 — Gate Stability Filtering (Extended)**

Under assumptions A1–A15 (M1), and assuming:
- the underlying system satisfies T1 (stability condition)
- the runtime projection certificate $P_t$ remains valid (i.e. $P_t.\text{domain\_valid} = \text{True}$)
- the Gate and final decision composition enforce the constraints (C1)–(C7) below

Then the Gate prevents execution of locally destabilizing or invalid transitions.

### Constraints Enforced by the Gate

**(C1) Lyapunov constraint**  
$$
\Delta W_t > 0 \quad \Rightarrow \quad v_t^{\text{gate}} \neq \text{ALLOW}
$$

**(C2) Projection validity constraint**  
$$
P_t.\text{domain\_valid} = \text{False} \quad \Rightarrow \quad v_t^{\text{gate}} = \text{ABSTAIN}
$$

**(C3) Projection boundary constraint**  
$$
\text{margin}(P_t) < \epsilon \quad \Rightarrow \quad v_t^{\text{gate}} \neq \text{ALLOW}
$$

**(C4) Adaptive instability constraint**  
$$
\kappa^t \leq 0 \quad \Rightarrow \quad v_t^{\text{gate}} = \text{ABSTAIN}
$$

**(C5) Switching stability constraint**  
switching violation $\quad \Rightarrow \quad v_t^{\text{gate}} \neq \text{ALLOW}$

**(C6) Exponential bound constraint**  
$$
\frac{W_{t+1}}{W_t} > \text{threshold} \quad \Rightarrow \quad v_t^{\text{gate}} \neq \text{ALLOW}
$$

**(C7) Projection monotonicity constraint (Π_ctrl)**  
$$
v_t^{\text{gate}} = \text{ABSTAIN} \quad \Rightarrow \quad v_t^{\text{final}} = \text{ABSTAIN}
$$

---

## 5. Projection-Aware Safety Layer (Π_cert)

The Gate integrates a projection safety layer based on the runtime certificate:

$$
P_t = (\text{domain\_valid}, \text{margin}, \text{is\_projection\_safe})
$$

This layer enforces:

- **Hard invalidity block**  
  $\text{domain\_valid} = \text{False} \implies \text{ABSTAIN}$

- **Boundary protection**  
  $0 \leq \text{margin} < \epsilon \quad \Rightarrow \quad \text{REQUIRE CONFIRMATION}$

- **Coupled instability rejection**  
  $\neg P_t.\text{is\_projection\_safe} \land (\Delta W_t > 0 \lor \text{global unsafe} \lor \text{switching unsafe}) \quad \Rightarrow \quad v_t^{\text{gate}} \neq \text{ALLOW}$

**Interpretation**:  
The Gate is not only stability-aware — it is also **projection-aware**.

---

## 5.1 Projection-Control Layer (Π_ctrl)

In addition to projection certification (P_t), the Gate integrates a projection-control layer:

$
v_t^{\pi} = \Pi_{\text{ctrl}}(x_t,z_t,H_t)
$$

This layer:
- operates on structured projected state
- produces a decision-level constraint
- is applied after all core gate layers

---

### Override rule

$$
v_t^{\text{final}} = \min_{\succ}\big(v_t^{\text{gate}}, v_t^{\pi}\big)
$$

---

### Monotonic restriction property

**Projection control monotonicity**

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}}
$$

equivalently, $\Pi_{\text{ctrl}}$ can only:
- keep the same decision
- downgrade it (ALLOW → CONFIRM → ABSTAIN)
- never upgrade it

---

### Strong safety invariant (IMPLEMENTATION CRITICAL)

**Irreversibility of abstention**

$$
v_t^{\text{gate}} = \text{ABSTAIN} \quad \Rightarrow \quad v_t^{\text{final}} = \text{ABSTAIN}
$$

This is strictly enforced in implementation:
Π_ctrl cannot relax an abstention decision.

---

### Interpretation

Π_ctrl acts as a *structured cognitive safety filter* on top of the Gate.

It enforces high-level consistency constraints that are not captured by Lyapunov signals.

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
v_t^{\text{gate}} \neq \text{ALLOW}
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

More precisely, at the decision level:

$$
\text{kappa violation} \quad \Rightarrow \quad v_t^{\text{gate}} = \text{ABSTAIN}
$$

This is a **design constraint**, not a theorem.

---

## 9. Monotonic Safety Property

The decision system satisfies:

$$
\text{ABSTAIN} \succ \text{REQUIRE CONFIRMATION} \succ \text{ALLOW}
$$

This guarantees that more restrictive decisions always dominate less restrictive ones.

This property is preserved by the final composition with projection-control overrides (Π_ctrl).

---

## 10. Relation to Global Stability

If:
- the base system is stable (T1 holds)
- the runtime projection certificate remains valid ($P_t.\text{domain\_valid} = \text{True}$)
- the Gate and the final composition layer enforce constraints (C1)–(C7)

then the combined system preserves **practical stability with high probability**.

---

## 11. Interpretation

The Gate does not guarantee stability by itself.  

Instead, the ARVIS decision stack acts as a **multi-layer safety filter** combining:
 
- Lyapunov filtering
- adaptive detection
- projection validation
- runtime diagnostics
- projection-control constraints (Π_ctrl)

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

The Gate / decision layer is:
- a stability-aware decision filter
- a projection-aware safety layer (Π_cert + Π_ctrl)
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