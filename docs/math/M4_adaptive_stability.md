# ARVIS — M4: Adaptive Effective Stability Estimation

## Objective

This document defines the first adaptive extension of the ARVIS stability core.

It introduces:

1. an online estimator of the effective contraction coefficient,
2. an adaptive stability condition,
3. a runtime interpretation of local stability margins.

This extension is designed to remain consistent with the existing ARVIS core:

\[
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
\]

and the switching stability condition:

\[
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
\]

while making the theory responsive to observed runtime trajectories.

---

## 1. Motivation

The current ARVIS core uses a static effective contraction parameter.

This is mathematically clean, but operationally limited:

- the true local contraction may vary over time,
- switching behavior may evolve by regime,
- perturbation intensity may change,
- projection quality may fluctuate across the validated domain.

Therefore, a static \( \kappa_{\mathrm{eff}} \) is useful as a baseline, but insufficient as the final runtime quantity.

---

## 2. Local Observed Decay Model

We model the observed Lyapunov evolution locally as:

\[
W_{t+1} \le (1-\kappa_t) W_t + \xi_t
\]

where:

- \( W_t \ge 0 \) is the composite Lyapunov energy,
- \( \kappa_t \in [0,1) \) is a local effective decay coefficient,
- \( \xi_t \ge 0 \) aggregates mismatch, noise, switching jumps, and projection residuals.

Ignoring perturbation for a first estimator yields:

\[
\widehat{\kappa}_t^{raw} = 1 - \frac{W_{t+1}}{W_t}
\]

for \( W_t > \varepsilon \).

---

## 3. Clipped Estimator

To avoid pathological values, define:

\[
\widehat{\kappa}_t^{clip} =
\mathrm{clip}\left(1 - \frac{W_{t+1}}{W_t}, \kappa_{\min}, \kappa_{\max}\right)
\]

with:

- \( 0 \le \kappa_{\min} < \kappa_{\max} < 1 \)

This clipping prevents:
- division instability,
- spurious explosive positive values,
- invalid values above 1.

---

## 4. Smoothed Adaptive Estimator

Define the online estimate recursively:

\[
\widehat{\kappa}_{t+1} =
(1-\rho)\widehat{\kappa}_t + \rho \widehat{\kappa}_t^{clip}
\]

with smoothing factor \( \rho \in (0,1] \).

Interpretation:
- small \( \rho \): conservative, smoother estimate,
- large \( \rho \): faster adaptation.

---

## 5. Adaptive Small-Gain Condition

We define the adaptive switching margin:

\[
S_t = \frac{\log J_t}{\tau_d(t)} + \log(1-\widehat{\kappa}_{\mathrm{eff}}(t))
\]

and interpret:

- \( S_t < 0 \): locally stable regime
- \( S_t \approx 0 \): marginal regime
- \( S_t > 0 \): locally unstable regime

This is not yet a full theorem of adaptive global stability.
It is a runtime adaptive criterion aligned with the static ARVIS core.

---

## 6. Conservative Runtime Principle

The adaptive runtime estimator must satisfy:

1. bounded output,
2. monotone degradation under observed energy growth,
3. conservative handling near \( W_t = 0 \),
4. explicit “estimation unavailable” state when data are insufficient.

---

## 7. Scope of Claim

At this stage, ARVIS does **not** yet claim:

- a full theorem of adaptive global exponential stability,
- a proof of convergence of the estimator itself,
- a proof under arbitrary switching.

At this stage, ARVIS claims only:

> the existence of a bounded, observable, implementation-aligned adaptive estimator of local effective contraction.

---

## 8. Next Mathematical Step

The next theorem-level goal is to prove that if:

1. \( \widehat{\kappa}_{\mathrm{eff}}(t) \) tracks \( \kappa_t \) with bounded error,
2. switching remains sufficiently slow,
3. perturbation remains bounded,

then an adaptive version of the ARVIS small-gain condition implies practical exponential stability on the validated domain.

---