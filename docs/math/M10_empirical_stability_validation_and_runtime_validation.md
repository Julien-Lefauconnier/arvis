# M10: Empirical Stability Validation Protocol and Campaign Report

> **Status: protocol executed on a synthetic corpus; report in
> section 10.** Sections 1 to 9 are the registered protocol,
> unchanged. Campaign MATH-B (2026-09-01) executed it on the
> deterministic synthetic corpus $\mathcal{D}$ = D-1.0 with
> pre-registered thresholds; section 10 records the observed values,
> the judgment and the mechanism findings. Only the status pointers
> of sections 2, 5 and 9 were updated to reference section 10; no
> criterion of the registered protocol changed. **Scope of the empirical
> claim, precisely: the campaign validates the measurement harness
> and the kernel's decision mechanics under controlled synthetic
> dynamics. It is not evidence about production traffic**, and the
> certification level vocabulary of the runtime is still the only
> stability attestation ARVIS makes about deployed behavior. The
> offline Phase A of the projection layer remains documented in
> `M3_appendix_projection_validation.md`.

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
| M10     | Empirical, runtime, closed loop   | **Executed on D-1.0 (sec. 10)** |

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

Every subsection states the metric and the criterion the runtime has
to satisfy. The observed values are recorded in section 10.

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

These four conditions were met by campaign MATH-B; section 10 is the
record. The certification level vocabulary of the runtime
(`VERSIONING.md`, certification levels) remains the only stability
attestation ARVIS makes about deployed behavior.

---

## 10. Campaign Report: MATH-B, 2026-09-01

### 10.1 Identity and registration

- Corpus: $\mathcal{D}$ = **D-1.0**, master seed 20260901, 7 families
  (nominal, boundary, adversarial, switching_stress, long_horizon,
  conflicting, declared_risk), 56 trajectories, 1440 turns. Generator,
  seeds and manifest published under `validation/m10/`
  (`corpus_manifest.json`); the corpus is bit-for-bit reproducible
  (pinned by `tests/math/m10/`).
- Thresholds: 12 criteria proposed, then **registered unmodified by
  the project owner on 2026-09-01, before any full-corpus run**
  (`validation/m10/thresholds.py`, decision DM-B2).
- Harness: closed-loop, pipeline level. Each turn runs a real
  `CognitivePipeline`; the harness threads the scientific state, the
  fast and slow Lyapunov states, the switching runtime and the
  adaptive observer across turns (the host role). The declared_risk
  family deliberately runs unthreaded. No LLM anywhere; fully
  deterministic; runs in seconds.
- Reproduction: `python -m validation.m10 run` then
  `python -m validation.m10 sweep` (Python 3.11+, no network). The
  per-turn measurements (3 MB) regenerate identically rather than
  being tracked.

### 10.2 Judgment against the registered thresholds

**11 of 12 criteria passed.** Per the registration discipline, the
failure is reported as a failure and the thresholds were not revised
after observation.

| Criterion (section) | Registered | Observed | Verdict |
|---|---|---|---|
| 5.1 nominal contraction dominates | >= 0.60 | 0.516 | **FAIL** |
| 5.1 bounded expansion | <= 1.50 | 0.563 | pass |
| 5.2 no divergent trajectory | == 0 | 0 | pass |
| 5.2 bounded energy sup W | <= 6.0 | 1.496 | pass |
| 5.3 estimator availability | >= 0.50 | 0.833 | pass |
| 5.4 ABSTAIN never relaxed (M6) | == 0 | 0 | pass |
| 5.5 adversarial ALLOW share | <= 0 | 0.0 | pass |
| 5.5 ALLOW given expansion | <= 0.05 | 0.0 | pass |
| 5.6 override data present | >= 1 | 1440 | pass |
| 5.7 negative feedback consistency | >= 0.95 | 1.00 | pass |
| 5.8 bounded projection component | <= 10.0 | 0.0 | pass |
| 5.9 envelope alive in domain | >= 0.10 | 0.176 | pass |

The failed criterion is substantive and instructive: on the nominal
family the observation axes follow a bounded exogenous walk, and the
composite energy the gate consumes tracks them. Nothing in the
closed loop pulls the corpus's observations toward equilibrium (the
loop adjusts verdicts, not the synthetic inputs), so contraction
events sit near one half (0.516) instead of dominating. The
criterion, as registered, measured a property of the corpus's
dynamics rather than of the kernel. It stays failed on D-1.0; a
future corpus revision should encode the intended contraction regime
in the input dynamics (state-feedback synthetic inputs), and the
lesson is recorded here rather than papered over.

Disclosed instrument correction: run 1's distribution encoder
omitted verdicts with zero share, so the two zero-observation
criteria of 5.5 resolved to missing data and scored FAIL under the
fail-closed judge even though the observed ALLOW mass was exactly
zero in both. The encoder now emits every canonical verdict with an
explicit share; the registered thresholds were untouched, and run
1's judgment is preserved as
`validation/m10/artifacts/judgment_run1_encoder_defect.json`.

### 10.3 Verdict distribution observed on D-1.0

Overall: ABSTAIN 85.6%, REQUIRE_CONFIRMATION 14.4%, **ALLOW 0.0%**
(0 of 1440 turns). The refusal-shaped criteria pass trivially in
such a regime, which is why the mechanism findings of 10.5 matter
more than the marginals: the corpus exercises the fail-closed side
of the gate far more than its permissive side.

The declared_risk family shows the graded input-risk ladder with
zero bleed between bands: declared risk in the allow band produced
REQUIRE_CONFIRMATION on 59/59 turns, the confirm band
REQUIRE_CONFIRMATION on 76/76, the block band ABSTAIN on 57/57.
Monotone, deterministic, no crossovers. The ALLOW rung itself is
unreachable on this corpus: the pre-verdict floor is already
REQUIRE_CONFIRMATION on a cold pipeline (`switching_unsafe_monitoring`,
`projection_boundary`), and the low-band relaxation is then refused
by the provenance guard (`input_risk_relax_denied`,
`verdict_provenance_not_artifact`). Both are fail-closed guards
working as specified; the graded ladder is effectively two-level on
synthetic turns.

### 10.4 Measured constants (LOT B2, report-only per DM-B1)

M13 flags the constants of assumption A12 as assumed, not measured.
This campaign measured both on D-1.0; per decision DM-B1 the values
are published here and in `constants.json` and **no runtime default
changes** (calibration on real traffic remains reserved, decision
DM4).

- Contraction factor $\alpha$ (nominal family, per-step
  $1 - W_{t+1}/W_t$ over 99 contracting pairs): median 0.348,
  p10 0.091, p90 0.622; contraction share of steps 0.538.
- Target-map Lipschitz constant $L_T$ (4000 sampled ratios over an
  explicit, published input metric on symbolic states): median
  0.126, p99 0.360, max 0.736, against the assumed 1.0.
- Small-gain margin $\kappa_{eff} = \alpha - \gamma_z \eta L_T$:
  assumed 0.13; at the conservative quantiles (alpha at p10, L_T at
  p99) the measured value is **0.084 > 0**. The small-gain condition
  survives measurement on D-1.0 with a reduced but positive margin.
  Caveats: alpha is conditioned on contracting steps of a synthetic
  family; L_T depends on the declared input metric; neither is a
  production estimate.

### 10.5 Mechanism findings

1. **The adaptive layer was structurally dead and is now live
   (DM-B0).** The MATH-A rename split the estimator snapshot into
   `kappa_raw/kappa_clipped/kappa_smoothed`; the runtime observer
   kept reading the historical `kappa_eff` field through a silent
   `getattr`, so the whole layer (kappa bands, confirmation forcing,
   ABSTAIN veto, recovery-relaxation block) never fired on a live
   path. Fixed RED-first during this campaign, direction verified
   strictly hardening on every consumer. No previously green test
   moved, which quantifies how far the live conditions were from the
   suite's reach; the m10 harness now pins layer liveness.
2. **Once live, the adaptive hard veto dominates non-contracting
   dynamics.** With margins $\ln(J)/\tau_d + \ln(1-\kappa)$ mostly
   positive on a corpus whose energy does not contract (mean margin
   +0.137; bands: hard 1107, critical 51, warning 16, stable 26 of
   1200 available turns), the final verdict source is the hard
   adaptive veto on 952 of 1248 threaded turns. This is the
   fail-closed reading of A12 doing exactly what it says under
   sustained non-contraction; on real, partly contracting traffic
   the band mix is an open measurement (DM4).
3. **Cold-start evidence, quantified.** An unthreaded turn faces an
   evidence-free PAC ceiling: risk_ucb = 1.0 on all 192 unthreaded
   turns, hence a CRITICAL risk verdict whatever the declared risk.
   Warming the estimator (threading only the scientific state)
   halves CRITICAL to 58.3% with 41.7% WARN and moves no final
   verdict at all on this family: the monitor's risk verdict is
   observability, not gating, on D. At the default
   $\delta = 0.01$, certifying OK ($\leq 0.15$) needs on the order
   of 100 clean turns; 24-turn trajectories cannot reach it.
4. **The composite fast-energy shortcut discards slow coupling
   exactly when the state is complete** (found in LOT B1, kept
   as-is): on complete quadruples the gate consumes the fast energy
   directly and the slow term only enters on incomplete states. The
   corpus therefore exercises the fast path; the slow-coupling term
   of M7 remains validated only by unit fixtures.

### 10.6 Sensitivity (LOT B4)

Published in `sweeps.json`:

- **Adaptive veto edge (margin 0)**: 92.3% of available margins sit
  above the edge; only 11.3% sit within +-0.02 of it. The veto's
  dominance on D is structural, not a hair-trigger boundary effect;
  moving the critical/warning band edges (-0.02, -0.05) reallocates
  under 4% of mass.
- **Collapse-abstain threshold 0.8**: flip mass at most 1.5% across
  alternates 0.7 to 0.9; the collapse signal is close to bimodal on
  D and the threshold choice is robust there.
- **Risk-verdict ceilings on the warm variant**: the ok ceiling
  (0.10/0.15/0.20) changes nothing on D (the UCB never gets low
  enough); the critical ceiling (0.30/0.40/0.50) moves the
  CRITICAL/WARN split (100%/58%/38% CRITICAL) and, on this corpus,
  never a final verdict.

### 10.7 What this campaign does not establish

Section 8's list stands. In particular: no claim about production
or veramem traffic (the corpus is synthetic and its nominal dynamics
proved exogenous rather than contracting); no adversarial-robustness
claim beyond the corpus's schema-level adversarial family; no
calibration of runtime defaults (DM-B1, DM4); and the ALLOW side of
the gate distribution is untested at this level because ALLOW is
unreachable on cold synthetic turns by design of the provenance and
monitoring guards.
