# M10: Empirical Stability Validation Protocol (planned)

> **Status: protocol, not results.** This document specifies the runtime
> empirical validation campaign for the ARVIS stability stack. **The
> campaign has not been executed**: no metric below has an observed
> value, and nothing in this document should be read as an empirical
> claim. The only empirical validation that exists today is the offline
> Phase A of the projection layer, on a deterministic fixture corpus,
> documented in `M3_appendix_projection_validation.md` and executed by
> the suite under `tests/math/`.

## 1. Objective

Define the empirical validation layer of the ARVIS Cognitive Operating
System: the dataset, the metrics, the pass criteria and the publication
requirements under which the theoretical results of M6–M9 would gain
runtime empirical support.

When executed, this protocol is intended to provide:
- quantitative confrontation of the theoretical results of M6–M9 with
  observed runtime behavior,
- runtime characterization of stability behavior,
- statistical assessment of robustness and practical stability claims,
- an evidence-backed description of the validity envelope under
  realistic conditions.

---

## 2. Position in the ARVIS Mathematical Stack

| Layer   | Nature                            | Status                       |
|---------|-----------------------------------|------------------------------|
| M0–M9   | Theoretical / structural          | Written, self-consistent     |
| M3 Phase A | Empirical, offline, projection layer | Executed (`tests/math/`) |
| M10     | Empirical, runtime, closed loop   | **Protocol only, not run**   |

---

## 3. Validation Scope

All metrics of this protocol apply exclusively to trajectories that
remain inside the validated projection domain:

$$
\forall t, \quad o_t \in \mathcal{O}_{\text{valid}}
$$

as defined and bounded in M3.

### 3.1 System Under Test

The evaluated closed-loop pipeline is:

$$
o_t \ \xrightarrow{\Pi}\ (x_t,\ z_t,\ q_t,\ w_t)\ \to\ W_t\ \to\ \widehat{\kappa}_t\ \to\ v_t^{\text{gate}} \ \to\ v_t^{\text{final}} \ \to\ u_t
$$

with:

$$
v_t^{\text{final}} = \min_{\succ}(v_t^{\text{gate}},\ v_t^{\pi})
$$

including in particular:
- projection layer ($\Pi$)
- composite Lyapunov evaluation
- adaptive $\kappa$ estimator
- GateStage (verdict computation)
- PiBasedGate (projection-control layer $\Pi_{\text{ctrl}}$)
- control modulation layer

---

## 4. Validation Dataset (to be constructed)

### 4.1 Dataset Construction

A deterministic, reproducible validation corpus $\mathcal{D}$ will be
constructed, containing:
- nominal (healthy) trajectories
- boundary / edge-of-domain cases
- adversarial-style perturbations (bounded)
- high-frequency switching stress cases
- memory-intensive / long-horizon cases
- conflicting or inconsistent signal inputs

### 4.2 Dataset Requirements

$$
\mathcal{D} = \{ o_{0:T_i}^{(i)} \}_{i=1}^N
$$

with:
- bounded trajectory lengths $T_i$
- perfect reproducibility (fixed, published seeds; deterministic
  projection)
- intentional coverage of the projection domain corners and interior

The corpus, its seeds and its generator are versioned artifacts: the
campaign is not considered executed unless a third party can regenerate
$\mathcal{D}$ bit-for-bit and rerun every metric.

---

## 5. Metrics and Pass Criteria

Every subsection states the metric and the criterion the runtime would
have to satisfy. None of these has an observed value yet.

### 5.1 Lyapunov Evolution

**Metric**: $\Delta W_t = W_{t+1} - W_t$

**Evaluations**:
- full distribution of $\Delta W_t$
- proportions: $P(\Delta W_t < 0)$ (contraction),
  $P(\Delta W_t \approx 0)$ (marginal), $P(\Delta W_t > 0)$ (expansion)

**Pass criterion**: contraction events dominate; positive excursions
are bounded and rare, with the thresholds fixed and published before
the campaign runs.

### 5.2 ISS Residual Bound

**Metric**:
$W(t) - C e^{-\beta t} W(0)$ and the empirical gain
$\Gamma = \sup_t W(t) / \sup_{k \leq t} \|w_k\|$

**Pass criterion**:
- bounded empirical gain $\Gamma$
- no divergence on $\mathcal{O}_{\text{valid}}$
- a practical residual tube of the form
  $W(t) \leq \Gamma(\bar{w}) + r$ with published constants

### 5.3 Adaptive Stability Estimation

**Metric**: $\widehat{\kappa}_t$ (smoothed adaptive contraction
estimate)

**Evaluations**:
- distribution of $\widehat{\kappa}_t$
- regime frequencies (stable / marginal / unstable)
- adaptive margin $m_t = \widehat{\kappa}_t - \kappa_{\text{threshold}}$

**Pass criterion**: the stable regime dominates; the critical regime
is localized near domain boundaries; the unstable regime is rare and
transient, per pre-registered thresholds.

### 5.4 Kappa Violation Frequency

**Metric**: $P(\kappa^t < \kappa_{\text{threshold}})$

**Pass criteria**:
- violation frequency below a pre-registered bound
- violations associated with adversarial inputs, projection edge cases
  or switching boundary conditions
- **hard invariant of M6, checked on every violation**: whenever a
  violation occurs, the gate abstains:

$$
v_t^{\text{gate}} = \text{ABSTAIN} \Rightarrow v_t^{\text{final}} = \text{ABSTAIN}
$$

### 5.5 Gate Behavior Distribution

**Metric**:
$v_t^{\text{final}} \in \{\text{ALLOW}, \text{REQUIRE\_CONFIRMATION}, \text{ABSTAIN}\}$

**Evaluations**:
- marginal frequency of each verdict
- conditional probabilities $P(v_t \mid \Delta W_t, \widehat{\kappa}_t)$

**Pass criterion**: ALLOW dominates in the stable regime,
REQUIRE\_CONFIRMATION concentrates near marginal zones, ABSTAIN
concentrates in regions of detected instability: the gate behaves as a
monotone stability filter.

### 5.6 Projection-Control Overrides

**Metrics**:

$$
P(v_t^{\pi}), \qquad P(v_t^{\pi} \prec v_t^{\text{gate}}), \qquad P(v_t^{\text{final}} \prec v_t^{\text{gate}})
$$

**Purpose**:
- measure how often structural constraints dominate energy-based
  decisions
- quantify the contribution of $\Pi_{\text{ctrl}}$ in restricting
  unsafe transitions

### 5.7 Closed-Loop Feedback

**Invariant under test**:
$\Delta W_t > 0 \Longrightarrow u_t \downarrow$

**Pass criterion**: an increase in the Lyapunov value produces a
measurable decrease in aggressiveness ($\epsilon$) and exploration
scale, supporting the negative feedback loop claimed in M7.

### 5.8 Perturbation Decomposition

**Decomposition**:
$w_t = w_t^{\mathrm{proj}} + w_t^{\mathrm{noise}} + w_t^{\mathrm{switch}} + w_t^{\mathrm{adv}}$

**Pass criterion**: perturbation sources are identified and bounded;
no evidence of uncontrolled amplification.

### 5.9 Validity Envelope Compliance

**Metric**: $P(\mathcal{V}_t.\mathrm{valid})$ where $\mathcal{V}_t$ is
the runtime validity certificate.

**Pass criterion**: high compliance rate inside
$\mathcal{O}_{\mathrm{valid}}$, with every violation traced to a known
stress condition, supporting
$o_t \in \mathcal{O}_{\mathrm{valid}} \Longrightarrow \mathcal{V}_t.\mathrm{valid} = \mathrm{True}$.

---

## 6. Target Result Statement (hypothesis)

**T10 (to be established): Empirical Stability Validation**

Under:
- the validated projection domain (M3),
- bounded composite perturbations,
- the fully implemented GateStage and adaptive estimator (M4–M5),

the campaign would have to exhibit, on every tested trajectory:

$$
W(t) \leq C \, e^{-\beta t} \, W(0) + \Gamma_{\text{emp}}(\bar{w}) + r
$$

together with the structural filtering invariant:

$$
v_t^{\pi} = \text{ABSTAIN} \Rightarrow v_t^{\text{final}} = \text{ABSTAIN}
$$

and the monotone non-relaxation property of M11–M12:

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}}
$$

T10 remains a hypothesis until the campaign runs and its artifacts are
published.

---

## 7. Theoretical Results Awaiting Runtime Evidence

| Result | Theoretical claim              | Runtime empirical status |
|--------|--------------------------------|--------------------------|
| T6     | Gate stability preservation    | pending (this protocol)  |
| T7     | Closed-loop adaptive stability | pending (this protocol)  |
| T8     | Robust practical stability + ISS | pending (this protocol) |
| T9     | Global validity envelope       | pending (this protocol)  |
| T11–T12 | Decision monotonicity and stability algebra | pending (this protocol) |

The offline Phase A evidence for the projection layer itself (bounded,
locally Lipschitz, noise-robust, switching-stable, Lyapunov-compatible
on the fixture corpus) exists and is documented in
`M3_appendix_projection_validation.md`.

---

## 8. What This Protocol Will Not Establish

Even fully executed, this campaign does not prove or claim:
- global stability outside $\mathcal{O}_{\text{valid}}$
- worst-case adversarial resilience (minimax sense)
- asymptotic convergence guarantees for **all** possible trajectories
- tightness of the residual tube constants

And as long as it is not executed, **no ARVIS release should be read as
certifying runtime stability behavior beyond what `VERSIONING.md`
states**: the projection certificate's noise robustness and mode
stability axes are not assessed, and `noise_gain_estimate` is always
`None`.

---

## 9. Execution and Publication Requirements

The campaign is considered executed only when, together:

1. the corpus $\mathcal{D}$, its generator and its seeds are published
   as versioned artifacts;
2. every metric of section 5 has an observed value with its
   pre-registered threshold;
3. the full run is reproducible bit-for-bit by a third party;
4. the results are recorded in this document (turning it from protocol
   to report) with a changelog entry.

Until then, this document is a protocol, and the certification level
vocabulary of the runtime (`VERSIONING.md`, certification levels) is
the only stability attestation ARVIS makes.
