# M6 — Gate Stability Filtering & Decision Consistency

## 1. Objective

This document defines the role of the **Gate operator** in ARVIS.

The Gate does not generate dynamics.

It acts as a **filter on admissible system evolution**, based on stability-related signals.

---

## 2. Gate as a Decision Filter

We define:

$$
G : (W_t, \Delta W_t, \kappa^t, H_t) \mapsto v_t
$$

where:

- $v_t \in \{\text{ALLOW}, \text{CONFIRM}, \text{ABSTAIN}\}$

The Gate does not modify the state directly.

It constrains which transitions are allowed.

---

## 3. Decision Structure

(ta partie actuelle est bonne → on garde avec mini ajustements)

---

## 4. Gate Semantics (CRUCIAL)

Each decision corresponds to a constraint on system evolution:

- **ALLOW** → no restriction
- **CONFIRM** → delayed / constrained evolution
- **ABSTAIN** → transition is blocked or replaced

The exact effect depends on the pipeline implementation.

---

## 5. Main Result — Conditional Filtering Property

### Result T6 — Gate Stability Filtering

Under assumptions A1–A15 (M1), and assuming:

- the underlying system satisfies T1 (stability condition)
- the projection Π remains within the valid domain
- the Gate enforces:

$$
\Delta W_t > 0 \Rightarrow v_t \neq \text{ALLOW}
$$

then:

> The Gate prevents execution of locally destabilizing transitions.

---

## 6. Interpretation

The Gate does not guarantee stability by itself.

Instead:

> It reduces the probability of unstable evolution by filtering unsafe transitions.

---

## 7. Relation to Global Stability

If:

- the base system is stable (T1 holds)
- the Gate blocks all locally increasing Lyapunov steps

then:

> the combined system preserves practical stability.

This result is **conditional** and depends on:

- correctness of Π
- validity of assumptions
- correct enforcement of Gate decisions

---

## 8. Adaptive Layer

The adaptive score:

$$
S_t = \tau_d \log J + \log(1 - \kappa^t)
$$

is used as a **runtime indicator**.

It is not a certified estimate.

---

## 9. Kappa Invariant

The hard invariant:

$$
\kappa\text{-violation} \Rightarrow \text{ABSTAIN}
$$

ensures:

> no transition is accepted when contraction is violated.

This is a **design constraint**, not a theoretical guarantee.

---

## 10. Monotonic Safety Property

The fusion operator satisfies:

$$
\text{ABSTAIN} \succ \text{CONFIRM} \succ \text{ALLOW}
$$

ensuring that:

> more restrictive decisions dominate less restrictive ones.

---

## 11. Limitations

The Gate does not:

- guarantee global stability
- ensure correctness of projection Π
- validate assumptions A1–A15
- provide formal certification

---

## 12. Summary

The Gate is:

- a **stability-aware decision filter**
- a **runtime enforcement layer**
- a **safety mechanism**, not a proof system