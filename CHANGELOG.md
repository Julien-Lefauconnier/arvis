
# Changelog

All notable changes to ARVIS are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [PEP 440](https://peps.python.org/pep-0440/)
versioning during the alpha.

## [Unreleased]

## [0.1.0a11] - 2026-07-19

Campaign 8 seals the complete effect-selection context. A capability is now
bound not only to its frozen payload and authorization, but also to the exact
principal, tenant, authentication provenance, service/session and runtime
identity under which it was minted. The campaign also closes enum/scalar
canonical collisions and removes residual test-only production surfaces.

### Security

- Introduced immutable `AuthorizedEffectContext` material and removed the raw
  pipeline context from `ToolInvocation`, validation and legacy execution
  payloads. Invocation, capability and intent now commit the exact principal,
  tenant, authentication provenance, service/session and runtime bindings.
- `SyscallHandler` compares the current trusted identity with the sealed effect
  context before intent creation. Divergence revokes the capability, releases
  confirmation and produces no receipt or effect; `KERNEL_PRINCIPAL` is
  excluded from user tool effects. The final audit also pins the optional host
  binding commitment in this equality check.
- Canonicalization v3 dispatches `Enum`, `StrEnum`, `IntEnum`, `Flag` and
  `IntFlag` before scalar parents and preserves enum mapping-key identity.
  Redaction policy v5, commitment v5 and confirmation format v4 invalidate old
  hashes and confirmations explicitly.
- Removed production-packaged test effect routes and replaced security-sensitive
  runtime assertions with explicit fail-closed checks, including under
  optimized Python.
- Pinned Bandit in the development gate, wired the same security command into
  CI, and added a wheel-content check that rejects OS metadata, bytecode,
  caches and packaged test helpers.

### Host integration

- Defined the ARVIS/Veramem boundary: ARVIS owns frozen effect material,
  authorization capabilities, intent/receipt validation, result binding and
  commitments. Veramem owns real authentication and tenant resolution,
  PostgreSQL persistence, persistent confirmation/idempotency coordination,
  business service injection and distributed workers.
- Tool dependencies must be constructor-injected. Mutable runtime context,
  credentials, database sessions and live clients are forbidden effect-context
  material.

## [0.1.0a10] - 2026-07-19

Campaign 7 hardens the complete external-effect transaction. The campaign began
with eight adversarial reproductions against `0.1.0a9`: capability mint
forgery, payload mutation after authorization, forged authorization wrappers,
capability reuse after outbox failure, leaked confirmation reservations, run-ID
prefix collisions, unstamped production principals and in-memory sinks accepted
as durable. Every reproduction is now a normal passing regression test.

### Security

- **Canonical frozen effect payload.** Authorization creates one deeply isolated,
  immutable `FrozenEffectPayload`. Confirmation, schema validation, policy,
  idempotency, intent commitment and execution all use that same canonical
  object. Mutation of caller-owned containers after authorization cannot change
  the dispatched effect.
- **Registered non-forgeable capabilities.** `AuthorizedInvocation` no longer
  transports a mint secret. Each nonce is registered against an exact commitment
  covering invocation, authorization snapshot, confirmation and idempotency
  material. Unknown, cloned, modified, foreign, revoked or consumed capabilities
  are refused atomically.
- **Strict authorization outcome.** `ToolAuthorizationOutcome` is frozen and
  accepts exactly one typed path: a manager-owned capability or a typed refusal
  with its own denial snapshot. Generic wrappers, repaired snapshots and duck
  typing are rejected before intent creation.
- **Receipt-activated transaction.** Authorization produces only a `MINTED`
  capability. `SyscallHandler` records the exact intent, validates the sink
  receipt and only then activates the capability. Sink failure, invalid receipt,
  durable-position replay or activation failure revokes the capability and
  prevents direct fallback execution.
- **Exception-safe confirmation lifecycle.** Confirmation reservation uses an
  explicit transaction. Every provable pre-effect refusal or exception releases
  the reservation; started, completed, failed or uncertain effects consume it
  conservatively. A forged capability cannot release another capability's
  reservation.
- **Authenticated production identity.** Production effects require a host-stamped
  `AuthenticatedPrincipal` matching the turn owner (or the reserved kernel
  principal). Authentication source, strength, service and session hash are
  committed into the effect material.
- **Qualified durable sink.** Production requires an `AuditSinkManifest` declaring
  a database or distributed-log sink that is transactional and append-only.
  `InMemoryAuditSink` is explicitly classified as memory and refused in that
  posture. Receipt store identity and durable positions are checked fail-closed.
- **Complete causal identity and effective idempotence.** Causal IDs now contain
  the complete run ID rather than a 48-bit prefix. The deterministic
  `idempotency_key` is committed into the intent, persisted in the outbox, bound
  by the receipt through `intent_sha256`, exposed to structured and legacy tool
  adapters and stable across retries.
- **No direct production effect route.** Public manager and executor methods can
  no longer mint, activate or dispatch a capability. One `SyscallHandler` claims
  the private effect boundary exactly once; the supported effect path is syscall
  mediated and outbox backed.

### Architecture

- Extracted `ToolAuthorizationService` for immutable request preparation and
  policy material.
- Extracted `IntentOutboxService` for intent construction, receipt validation,
  durable-position replay protection and local publication.
- Extracted `EffectDispatcher` for single-use capability consumption and explicit
  effect-boundary classification.
- Shared fail-closed tool schema validation lives in `arvis.tools.tool_schema`.
- `SyscallHandler.handle`, `_record_intent`, `ToolManager.authorize`,
  `ToolExecutor._execute_invocation` and `tool_execute` are now orchestration
  entrypoints guarded by maintainability ratchet tests.
- Added the normative governed-effect architecture note and updated tool
  lifecycle, runtime concurrency doctrine and architecture invariants.

### Breaking changes and host migration

- Re-pin Veramem and other hosts to `0.1.0a10`; capability, activation and intent
  commitments changed during the campaign.
- Do not call `ToolManager.run`, `execute_authorized`, `activate_authorized`,
  `ToolExecutor.execute_invocation` or `ToolExecutor.execute`; use `CognitiveOS`
  or the governed `SyscallHandler` path.
- Production effect contexts must use `AuthenticatedPrincipal`.
- Production sinks must expose a qualifying `AuditSinkManifest` and return an
  `AuditReceipt` with the exact complete `run_id`, `causal_id`, intent hash and
  matching store fingerprint.
- Persist the complete intent, including `idempotency_key`, and forward that key
  to the external system. Ensure causal-ID storage is not sized for the former
  twelve-character run prefix.
- Keep one ARVIS runtime instance per request/turn. Capability and confirmation
  registries are thread-safe within one process but are not distributed across
  workers.

## [0.1.0a9] - 2026-07-18

Campaign 6: external-audit remediation. An external audit of 0.1.0a8
(consolidated 9.3/10) left four thresholds open on the effect path:
the pre-effect intent was recorded before the business authorization
existed, results were not cryptographically bound to their intents,
the canonicalization domain was not fully injective, and the execution
capability was publicly mintable and reusable. This release closes all
four, plus the confirmation, durability, run-identity and hygiene
findings, each pinned with its reproduced attack vector in
`tests/adversarial/test_campaign6_audit_regression.py`.

### Security

- **P0: authorization before intent (Lot 1, a8 section 8).** The full
  business authorization (extraction, tool lookup, input schema,
  principal/tenant, confirmation reservation, ToolPolicy) now runs
  BEFORE the `tool.execute` syscall is issued
  (`ToolManager.authorize`); the verdict travels sealed on the minted
  `AuthorizedInvocation`; the pre-effect intent binds that exact
  verdict; the mutable `ctx.extra["tool_authorization_snapshot"]`
  channel is removed and a bare `tool.execute` without an
  authorization outcome is refused fail-closed. Every retry attempt is
  re-authorized, so a stale snapshot is unreachable by construction.
- **P0: result bound to its exact intent (Lot 2, a8 section 9).**
  Every journaled effect result carries the engagement digest of ITS
  intent (`intent_commitment_sha256`, stamped single-use by the
  handler); the bijection verifies the full tuple and refuses any
  permutation of same-syscall results; the journal digest (v2) binds
  ordered per-pair commitments, so a permutation changes the digest
  even though causal ids are envelope-stripped.
- **P0/P1: injective canonicalization domain closed (Lot 0, a8
  section 7).** Canonicalization v2: `bytearray` gets its own tag,
  path types and class identities are module-qualified, non-finite
  floats are refused, and underscore-prefixed private state is REFUSED
  rather than silently dropped (the explicit `__arvis_canonical__`
  serializer hook is the contract for private state). Downstream
  bumps: `REDACTION_POLICY_VERSION` 4, `COMMITMENT_VERSION` 4,
  `CONFIRMATION_FORMAT_VERSION` 3. No a8-era hash or confirmation is
  honoured. Property-based injectivity is enforced with Hypothesis.
- **P1: private, single-use capability (Lot 3, a8 section 10).
  BREAKING.** The minting authority is no longer a public attribute of
  `ToolExecutor`; the only handle is `claim_minting_authority()`,
  claimable exactly once (the `ToolManager` claims it at
  construction). Every capability carries a fresh nonce CONSUMED at
  execution: one authorization, one effect; a replayed capability is
  refused. `ToolExecutor` is removed from the `arvis.api` public
  exports.
- **P1: unique confirmation record commitment, mandatory TTL (Lot 4,
  a8 section 12).** Every issued confirmation computes
  `record_commitment = H(version, nonce, tool, payload_sha256,
  principal, tenant, issued_at, ttl, issuer)`; the proof binds THIS
  value, so two human decisions on the same effect never share a
  commitment. The TTL is mandatory and strictly positive (default
  300s); expired records are purged at reservation.
- **P1: durability proven, not declared (Lot 6, a8 section 14).
  BREAKING in durability-requiring profiles.** A durable sink now
  ANSWERS: `DurableAuditSink.append(intent)` returns an `AuditReceipt`
  binding exactly the persisted intent (engagement digest, run
  identity) and where it durably lives; the syscall boundary validates
  every receipt fail-closed. A bare callable sink is refused where
  durability is required; `InMemoryAuditSink` is the reference
  implementation. Exported on `arvis.api` for hosts.
- **Global run identity (Lot 5, a8 section 17).** A fresh unguessable
  `run_id` is generated at run entry, prefixes every causal id
  (global uniqueness across runs in a shared sink) and is journaled on
  every intent and result. It is ENVELOPE identity, stripped from the
  hashed material: the deterministic-commitment contract holds; the
  run <-> proof anchoring is the sink receipt's job. An accidental
  determinism (the raw artifact digest coinciding only through the id
  collision itself) is made intentional via the artifact's explicit
  canonical encoding.
- **Effect boundary classification (Lots 1/4, a8 constat 11).**
  `ToolResult.effect_boundary` distinguishes pre-effect refusals from
  crossed-boundary outcomes; a reserved confirmation is committed only
  when the boundary was crossed and released on any pre-effect refusal
  (schema violation, unknown tool, tool.validate refusal, policy
  denial): a human confirmation is never burned for an effect that
  never ran.

### Changed

- Invocation governance fields are filled (Lot 7, a8 section 13):
  `audit_required` travels from the tool spec; `consent_granted` comes
  from the trusted host composition channel `ctx.consent_granted`
  (host-stamped, string keys only, never request-facing extra);
  `idempotency_key` is derived deterministically and is stable across
  re-authorized retry attempts of the same logical action.
- The `assert` at the host declaration boundary is an explicit
  fail-closed raise (an assert vanishes under `python -O`; Bandit
  B101, a8 section 20).
- The engagement digest binds extracted effect parameters (tool name
  and payload, from the sealed invocation) instead of a lossy partial
  view of the runtime result object.

### Migration notes (hosts, veramem re-pin)

- `executor.authority` no longer exists; one `ToolManager` per
  executor; `from arvis.api import ToolExecutor` no longer resolves.
- A capability cannot be executed twice; syscall results carry
  `intent_commitment_sha256` and `run_id`.
- All commitments changed (canonicalization v2): any anchor stored
  under a8 is invalid; no a8 confirmation record is honoured.
- PRODUCTION-posture hosts must provide a `DurableAuditSink`
  (receipts), not a callable; the veramem realization is the
  PostgreSQL sink (chantier D4-e).
- `ToolConfirmation` gains `nonce`, `issued_at_unix`, `ttl_seconds`,
  `issuer` and `record_commitment`; `expires_at_monotonic` is no
  longer optional; `issue` refuses non-positive TTLs.


## [0.1.0a8] - 2026-07-17

Campaign 5: external-audit remediation. An external audit of 0.1.0a7
found a class of collision vulnerabilities in the effect-path
commitment machinery, plus gaps in confirmation lifecycle, journal
bijection, replay authentication and executor reachability. This
release closes them and moves the effect path from "high-level alpha"
toward an integrable kernel beta. Every reported P0 and P1 is closed
with a reproduced attack vector pinned as a regression test.

### Security

- **P0: injective canonicalization of effect material (Lot 0-1).** The
  a7 chain `deep_material -> _strip_volatile -> redact_for_commitment`
  reduced distinct business payloads to the same digest before
  SHA-256, so a confirmation granted to act on record-A could be
  consumed to act on record-B. A single injective encoder
  (`arvis.kernel_core.canonicalization`) now feeds every effect-path
  hash: type-preserving (`bytes`, `datetime`, `Decimal`, `UUID`,
  `Path`, `Enum`, sets, dataclasses each map distinctly), key-type
  preserving (`{1: x}` != `{"1": x}`), fail-closed on non-encodable
  values. `payload_commitment` and `effect_engagement_digest` are
  rebuilt on it; volatile stripping is confined to declared journal
  envelopes and never rewrites a business payload. A latent
  non-determinism (`process_id` in the engagement material) surfaced by
  the injective encoder is fixed by excluding runtime bindings
  explicitly. Bumps: `REDACTION_POLICY_VERSION` 2->3, `COMMITMENT_VERSION`
  2->3, `engagement_version` 1->2.

- **Generic host declaration channel (Lot 2).** New
  `arvis.kernel_core.host_declaration`: an opaque `host_context`
  (JSON-safe, canonicalized injectively) the host attaches to every
  governed intent, with `instance_label` as the one conventional key
  ARVIS reads (only to stamp boundary provenance on journaled intents,
  never in committed materials). Injected components may expose
  `governance_manifest()`, which `config_fingerprint` binds in full, so
  two differently configured components of the same class no longer
  share a fingerprint (audit constat 17).

- **P1-5: versioned, transactional confirmations (Lot 3).** Confirmation
  records carry an explicit `CONFIRMATION_FORMAT_VERSION` (starts at 2);
  a record of any other version is refused at reservation, so no a7-era
  confirmation is honoured. The lifecycle is two-phase
  `reserve -> commit / release`: the tool manager reserves before the
  policy, commits after the effect runs, and releases on a pre-effect
  denial, so a legitimate confirmation is never burned by a policy
  refusal and never double-spent. A `ToolAuthorizationSnapshot` (policy
  verdict, principal, tenant, risk, bound confirmation commitment) is
  bound into the effect engagement, so two identical effects authorized
  differently no longer share a commitment (audit constat 11).

- **P1-6: strict intent/result bijection (Lot 4).** New
  `arvis.kernel_core.syscalls.intent_result_bijection`: the commitment
  binds the journals only under an exact one-to-one correspondence.
  The a7 set-membership check missed duplicate intents, orphan results
  and syscall mismatches; the strict verifier requires exactly one
  intent and one result per causal id, agreeing on the syscall name,
  and fails closed as `audit_incomplete` on any deviation.

- **P1-7: authenticated replay (Lot 5).** BREAKING. The a7 `replay()`
  (optional expected commitment, so `replay_verified(ir)` accepted
  arbitrary fingerprints) is removed. `replay_verified(ir, *,
  expected_global_commitment)` makes the external anchor mandatory and
  authenticates the recomposed commitment against it;
  `replay_recomposed(ir)` recomposes without authenticating and is
  named for it. The expected commitment must come from a durable source
  outside the IR; the host owns that source's durability (documented
  host requirement).

- **P1-8: uncircumventable executor (Lot 6).** BREAKING. New opaque
  capability `AuthorizedInvocation`, minted only by the tool manager's
  `InvocationAuthority` after policy. `ToolExecutor.execute_invocation`
  runs a tool only from a verified capability; a bare invocation, a
  forged capability or one from another authority is refused. The
  `execute_authorized` rebuild-and-run bypass is removed, `execute()`
  forbids all direct execution, and `CognitiveOS.tool_executor` is no
  longer public. There is no path to an effect the policy did not
  authorize.

### Changed

- `CognitiveOS.replay(...)` removed; use `replay_verified(...)` (with a
  mandatory external commitment) or `replay_recomposed(...)`.
- `ToolExecutor.execute_authorized(...)` removed; tools run only through
  a manager-minted `AuthorizedInvocation`.
- `CognitiveOSConfig` gains `host_context`; `KernelServiceRegistry`
  gains `host_context` and `instance_label`.

## [0.1.0a7] - 2026-07-17

### Security

- **P0-2-a6: strict commitment_inputs validation.** The
  `commitment_inputs` block is validated fail-closed before any
  composition (`CommitmentInputs` frozen type,
  `validate_commitment_inputs`): exactly the four component keys, no
  extras, canonical lowercase sha256 hex values. A forged, incomplete
  or malformed block never composes into a formally valid commitment:
  it surfaces as an absent commitment with the dedicated reason
  `commitment_inputs_invalid`, refused under REQUIRED and flagged under
  DEGRADED. The permissive `.get(key)` composition is gone, and the
  exported block is the canonical validated form.

### Fixed

- **P0-4-a6: kernel-internal syscalls are functionally reachable.**
  `process.spawn`, `process.suspend`, `process.resume` and
  `interrupt.emit` now accept the uniform boundary contract
  (`ctx=None`, `causal_id=None`): the kernel principal on the trusted
  context channel reaches them, the intent outbox pairs with their
  results, and anything else stays denied. They were governed
  structurally but unreachable (denied without ctx, invalid-args with
  ctx). End-to-end tests now exercise the REAL registered syscalls with
  runtime objects, not probes (campaign-3 lesson applied).
- **P1-13-a6: normalized authorization boundary.** An exception raised
  by an access resolver or by the authorization policy no longer leaks
  through the syscall boundary: it is normalized into a journaled,
  fail-closed refusal with the stable reason code
  `authorization_failure`.

### Added

- **P0-3-a6: pre-effect engagement of exact parameters.** The intent
  outbox entry now carries `commitment_sha256`, computed BEFORE the
  effect runs: it binds the syscall, its materialized redacted
  arguments (`deep_material` walks object attributes so distinct
  payloads never collapse into a type marker), the principal, the
  tenant, the turn owner and the authorization outcome. Two effects
  with different parameters and identical results yield different
  composed commitments. Redaction policy bumps to v2 (tool and LLM
  payload fields covered: `tool_payload`, `arguments`, `messages`,
  `input_data`); the redaction primitives move to the kernel boundary
  (`arvis/kernel_core/syscalls/engagement.py`, re-exported unchanged
  from `arvis.api.commitment`). Commitment VALUES change (policy
  version is part of the hashed material). This closes the deferral
  documented at campaign-3 Lot 5.
- **Deterministic LLM prompt rendering (surfaced by the engagement
  digest).** The intent-enrichment prompt embedded a dataclass repr
  carrying `decided_at` (wall clock), making the LLM request, hence the
  pre-effect engagement, non-deterministic across identical runs. The
  prompt now renders the intent through an explicit deterministic
  projection excluding wall-clock fields; the `run_ir == to_ir`
  contract and cross-run commitment determinism hold again.
- **P0-1-a6: mandatory post-effect audit and intent/result bijection.**
  On the effect path the result journal is no longer best-effort: a
  journaling failure after an effect marks the execution
  AUDIT_INCOMPLETE (the effect happened; arvis refuses to pretend it
  proved it, never denies it retroactively). The intent/result
  bijection is verified where the journals are read
  (`_build_commitment_inputs`, decision D4-c): an effect intent without
  its paired journaled result, or the handler incompleteness flag,
  yields no commitment with the dedicated reason `audit_incomplete`;
  REQUIRED refuses the public result through the existing absence
  machinery (decision D4-b), DEGRADED flags it, and the view exposes
  `audit_incomplete`. The audit scenario (effect executed, journal
  down, REQUIRED commitment still produced) is closed and pinned by
  tests.
- **P1-5-a6: single invocation object from authorization to the tool.**
  The executor's canonical entry is now
  `execute_invocation(invocation, result, ctx)`: it receives the SAME
  `ToolInvocation` the policy evaluated, so user, principal, tenant,
  real turn risk, consent, audit and idempotency fields travel to the
  tool without reconstruction. `execute_authorized` remains as a
  deprecated compatibility path that rebuilds a minimal invocation and
  delegates. The direct-execution prohibition is unchanged.
- **P1-10-a6: bound, satisfiable tool confirmation (full object,
  decision D4-d).** New `arvis/tools/confirmation.py`:
  `ToolConfirmation` (frozen) binds a confirmation to the tool, the
  redacted payload hash, the principal, the tenant and a monotonic
  expiry; `ConfirmationRegistry` issues and consumes them with strict
  semantics (exact match on every binding, single use, expired records
  purged, a mismatch does NOT burn the record). `ToolInvocation` gains
  `confirmed`, `confirmation_id` and `confirmation_commitment`; the
  manager resolves the confirmation from the trusted composition
  channel (`ctx.confirmation_result`) against the registry, and the
  policy accepts a `requires_confirmation` spec only for a confirmed
  invocation. A tool declaring `requires_confirmation=True` was
  previously refused unconditionally; the host wires a registry through
  `CognitiveOSConfig.confirmation_registry`.
- **D4-e (P1-a6): effectful production requires a durable sink.** In
  the production profile, the first EFFECT syscall with no
  `audit_intent_sink` configured is refused at the point of use
  (reason `durable_sink_required`), before the intent is recorded and
  before the effect runs. A production profile without effects stays
  valid without a sink; local profiles never require one.

## [0.1.0a6] - 2026-07-17

### Fixed

- **Replay reproduces the governing postures.** The runtime profile
  that governed a run ("local", "production") is now recorded in
  `CognitiveContextIR.runtime_mode`, and the replay context builder
  reapplies the derived postures (global stability action, switching
  envelope, input-risk harden-only) from the record through a single
  shared helper (`apply_runtime_postures`), never from the replayer's
  environment (decision D-a extended to postures). Before this fix a
  production run whose verdict depended on a posture replayed with the
  permissive defaults and failed commitment verification. IR shape
  gains one context field; IR hash values change accordingly.

### Security

- **F-001-a5: a caller-declared risk never relaxes the verdict on a
  mixed payload.** The pure-scalar precondition of the input-risk policy
  is now coded (`is_pure_risk_payload`): the grading path (which may
  relax a sparse-projection artifact) is active only for a payload
  exclusively dedicated to the risk scalar (`{"risk": x}`). Any mixed
  payload is harden-only: the declared risk composes through
  `max_strictness`, the hardening is traced (`input_risk_harden`), and
  existing reasons are never superseded. The production profile sets the
  `harden_only` posture (`ctx.input_risk_mode`), so in production a
  declared risk never relaxes at all, pure payload included; unknown
  posture values fail closed to harden-only. Examples 02/04/09 moved to
  pure risk payloads; example 06 now demonstrates the harden-only
  doctrine on a real trade payload.

### Changed

- **F-002/F-003/F-004-a5: unified production invariants.** The
  PRODUCTION invariants now live in `CognitiveOSConfig.__post_init__`
  as the single source of truth: `audit_commitment_policy=REQUIRED` and
  no `runtime_controls`, whatever the constructor. A direct
  `CognitiveOSConfig(runtime_mode="production")` with the DEGRADED
  default is refused at construction, and a `production()` override
  that relaxes an invariant is refused rather than silently clamped.
  `CognitiveOS.config` is now a read-only property backed by a private
  `_config`: the runtime governs under the configuration it was built
  with, for its whole lifetime.

### Added

- **F-009-a5: mandatory access resolver for effect syscalls (closes the
  deferred B6 guard).** `register_syscall` refuses an EFFECT
  registration without an access resolver at import time: an ungoverned
  effect capability is structurally unreachable. Reference resolvers
  (`arvis/kernel_core/access/resolvers.py`) express each class's real
  rule under the single owner-scoped policy: kernel-internal syscalls
  (`interrupt.emit`, `process.*`) are owned by the runtime itself
  (reserved `KERNEL_OWNER_ID`; only `KERNEL_PRINCIPAL` on the trusted
  context channel passes, identity is never read from syscall
  arguments); turn-scoped syscalls (`tool.execute`, `llm.generate`) are
  owned by the turn's user, a stamped foreign principal is denied, and
  a call without an identifiable owner is denied fail-closed.
- **F-010-a5: governance manifest and enriched registry fingerprint.**
  `ToolRegistry.manifest()` describes the registered surface completely
  for governance: identity (registry name, implementation qualname,
  declared spec name) and every governance-relevant spec field
  (schemas as canonical sha256 hashes, never in clear; execution
  semantics; policy flags; capability manifest fields). The registry
  `fingerprint()` is now the sha256 of the canonical JSON manifest,
  versioned (`MANIFEST_SCHEMA_VERSION`); a non-canonicalizable declared
  schema refuses pinning (fail-closed). Fingerprint VALUES change with
  this release: hosts pinning the old name+qualname digest must re-pin
  (veramem: the `tool_registry_frozen` log hash changes, no functional
  impact, the engine-side registry is empty).
- **F-006-a5: complete invocation context (skeleton).** `ToolInvocation`
  gains opaque `principal`, `tenant` and `consent_granted` fields (host
  semantics, same doctrine as capability grants). The tool manager
  threads identity from the trusted context channel only (a stamped
  `Principal`; never request-facing extra), the bare `user_id` for
  owner scoping, and `risk_score` as the real turn risk: hardening
  composition of the declared input risk and the assessed collapse
  risk. The dormant `max_risk` spec policy becomes live and
  conservative: 0.0 only when no signal exists.
- **F-008-a5: durable audit intent before effect (outbox).** For any
  EFFECT syscall, the handler journals a `syscall_intent` entry BEFORE
  the call: structural metadata only (syscall name, causal id, tick,
  process id; no payload material), appended to the ordered
  `ctx.extra["syscall_intents"]` channel (paired with the result
  journal through the shared causal id) and emitted as a runtime event.
  A host `audit_intent_sink` (new `CognitiveOSConfig` field) is called
  synchronously with a copy of the entry before the effect; ANY failure
  to record the intent refuses the syscall
  (`reason_code=audit_intent_failed`, fail-closed). An intent without a
  paired artifact afterwards signals a crash during the effect: bounded,
  visible uncertainty. Authorization runs before the outbox: a denied
  effect never reaches it. Known gap carried to the composed-commitment
  lot: the timeline the current global commitment hashes is empty on a
  standard run (runtime events never reach `ctx.timeline`), so the
  intent/result journals will enter the commitment explicitly there.
- **F-007/F-018-a5: composed v2 global commitment with redaction before
  hash.** `arvis/api/commitment.py`: the global commitment is now the
  canonical hash of explicit named components with the version embedded:
  cognitive `ir_hash`, `timeline_commitment`, the digest of the REDACTED
  syscall journals (intents and results; content-bearing fields replaced
  by sha256 markers under the versioned `REDACTION_POLICY_VERSION`, so
  the audit gap of an environment-blind commitment over an empty
  timeline is closed by the journals entering explicitly), the registry
  manifest `fingerprint()`, the effective configuration fingerprint
  (governance fields; injected objects by presence and type identity
  only) and the active policy tables fingerprint. Replay (decision
  D-a): the non-cognitive components ride in the exported IR as a
  `commitment_inputs` block outside the cognitively hashed sections
  (`run_ir` carries it too; `run_ir == to_ir` holds); a replay
  recomposes from the declared block, never from the replayer's
  environment, so identical replay yields an identical commitment and a
  divergent environment stays detectable by comparison. Commitment
  VALUES change with this release. A missing component set yields
  `commitment_reason=commitment_inputs_unavailable` under the existing
  absence machinery (REQUIRED refuses, DEGRADED flags).

## [0.1.0a5] - 2026-07-16

Consolidation release (campaign 2): closes the composition-scope
findings of the 0.1.0a4 external audit around one invariant: the
enforcement phase of the gate stack is monotone
(ALLOW < REQUIRE_CONFIRMATION < ABSTAIN), and every sanctioned
exception is provenance-checked, traced and bounded.

### Added

- **Canonical verdict order and provenance (F-001 completion)**.
  `arvis/math/lyapunov/verdict_order.py` (strictness order,
  `max_strictness`, `is_relaxation`); provenance ledger and
  `enforce_monotone` guard in the gate trace helpers, wired around six
  enforcement gates; pipeline-level hypothesis property: the verdict
  transition trace never contains a relaxation outside the sanctioned,
  documented channels.
- **Versioned hard_block severity table (F-003)**
  (`arvis/math/stability/hard_block_policy.py`): stability reasons map
  to warning / confirmation / hard block; unknown reasons fail closed;
  the default table preserves the pre-A5 runtime behaviour and the
  applied table version is recorded in the trace.
- **Closed runtime mode set (F-008)** (`arvis/api/runtime_mode.py`,
  exported from `arvis.api` and the root): LOCAL, TEST, RESEARCH,
  PRODUCTION; unknown values are refused at configuration time.
- **Closed PRODUCTION profile (F-002, F-017, F-018, F-019)**.
  `CognitiveOSConfig.production()` fixes the mode and defaults the
  audit commitment policy to REQUIRED; production forces
  `global_stability_action="confirm"` and
  `switching_envelope_mode="enforce"` on every context, denies a tool
  declaring `required_consent` or `data_egress` when the matching gate
  is missing (config gains `consent_gate` / `egress_gate`), and
  freezes the tool registry automatically at the first run.
- **Tool effect governance (F-014, F-016, F-020)**. `timeout_seconds`
  is now a deadline on result acceptance (late result rejected with
  `ToolTimeoutError`; the effect may still have happened, interruption
  is a later chantier); automatic retry requires declared idempotence
  (a side-effectful, non-idempotent effect is never replayed, a
  missing spec means no automatic retry); declared input schemas are
  validated before the call and output schemas after it, each with its
  specific failure status, surfacing structural paths only (ZK).
- **Version coherence guard** (`tests/api/test_version_coherence.py`):
  the README Versioning table and the source-checkout fallback must
  equal `pyproject.toml`. **Runtime lifecycle contract**
  (`docs/architecture/RUNTIME_LIFECYCLE.md`): instance-per-request,
  unbounded reused-instance state (documentation side of F-022/F-023).

### Changed

- **Global stability policy is monotone (doctrine amendment)**. Under
  `action="confirm"`, global instability now hardens ALLOW to
  REQUIRE_CONFIRMATION (it previously did not), and the
  ABSTAIN -> REQUIRE_CONFIRMATION reinterpretation only applies to an
  ABSTAIN produced by the global stability axis itself (provenance
  checked, unknown provenance fails closed); a foreign veto
  (projection, kappa, memory, adaptive) is never relaxed. The
  campaign 1 doctrine of a blanket product transition is amended
  accordingly. The `gate_policy` confirm branch composes through
  `max_strictness`.
- **Fail-closed composition (F-005)**: a fusion failure abstains
  instead of falling back to the pre-fusion verdict; an unavailable
  validity envelope abstains; the input-risk gate abstains on
  exception and only relaxes sparse-projection artifacts (F-006,
  provenance checked); the PI override trace records applied
  transitions only.
- **Switching safety is honest (F-004)**: the hardcoded
  `effective_switching_safe = True` is replaced by a
  `switching_envelope_mode` knob ("soft" by default, unknown modes
  fail closed into enforcement; production sets "enforce").
- **Runtime configuration (F-007, F-009, F-012)**: `CognitiveOSConfig`
  is frozen; `force_tool` only selects a tool and execution requires
  an explicit `force_execution=True` (retries keep executing);
  `audit_commitment_policy=REQUIRED` with `enable_trace=False` is
  refused.
- **One registry**: the runtime and its `ToolManager` now govern the
  registry the host registered tools on (the runtime previously built
  its own empty registry and evaluated the tool policy against it).
- **Reproducible gate tooling**: `ruff==0.14.3`, `mypy==1.19.1`,
  `pytest==8.4.2` pinned in the dev extras (plugins stay unpinned
  until the dev lockfile lands); `types-jsonschema` added for the new
  runtime `jsonschema` use.

### Deferred

- Execution commitment chain (F-010, F-011, F-013, F-021, F-032):
  campaign 3, targeted at 0.1.0a6.
- LLM runtime governance (F-024 to F-031): dedicated campaign.

## [0.1.0a4] - 2026-07-16

Hardening release: the seven kernel-scope findings of the external
audit (F-001, F-002, F-004, F-009, F-010, F-013, F-015) plus the end
of the A2 context decomposition. One principle ties the safety lots
together: a failing guarantee mechanism can never relax.

### Added

- **TrustedRuntimeControls (F-001)**
  (`arvis/api/runtime_controls.py`, root export). Host-only controls
  (`force_tool`, `force_execution`, `force_safe_projection`,
  `force_safe_switching`) are injected by composition through
  `CognitiveOSConfig.runtime_controls` and rejected in the production
  runtime profile. Abuse tests assert that injecting any of the four
  keys through the request-facing `extra` channel is inert and that an
  ABSTAIN verdict can never be relaxed by overrides.
- **Governed tool registry (F-004, kernel part)**. `ToolRegistry.register`
  refuses re-registering an existing name unless an explicit
  `replace=True` is passed; `freeze()` locks the registry after
  bootstrap (any further mutation refused, explicit replacement
  included) and returns a deterministic, order-independent sha256
  fingerprint of the tool surface; `freeze_tools()` exposed on
  `CognitiveOS` and `ArvisEngine` for host-side pinning.
- **AuditCommitmentPolicy (F-015)** (`arvis/api/audit.py`, root
  export). The absence of an audit commitment is never silent: every
  result view carries the applied policy, a reason code when the
  commitment is missing (`ir_not_serializable`, `timeline_not_journal`,
  `timeline_commitment_failure`, `commitment_hash_failure`) and an
  explicit degradation flag. REQUIRED refuses an unauditable run
  (`ArvisSecurityError`), DEGRADED (default) records the visible
  degradation, OPTIONAL records the reason only. Threaded through
  `CognitiveOSConfig.audit_commitment_policy` to both the run and
  replay paths.
- **Packaging contract for the IR schema (F-010)**.
  `arvis/api/schema/ir_schema.json` now ships in the wheel
  (package-data) and the sdist (MANIFEST.in); the CI build job asserts
  the schema inside the built wheel and reads it back from an
  installed wheel through `importlib.resources`; pytest locks the
  canonical resource access path and both packaging declarations.
- **Fail-closed gate contract tests**
  (`tests/kernel/stages/test_gate_fail_closed.py`), including
  hypothesis property tests of the monotone strictness invariant
  ALLOW < REQUIRE_CONFIRMATION < ABSTAIN on the enforcement gates.
- **Audit artifact mutation guard**
  (`tests/api/test_audit_structures_immutable.py`): recursive mutation
  of an exported IR can never diverge the view from its commitment;
  replay does not mutate its input.

### Changed

- **Gates are fail-closed (F-002)**. An exception inside a verdict
  gate (projection enforcement, kappa hard block, global stability
  policy, validity enforcement) now forces ABSTAIN with a traced
  verdict transition (`*_fail_closed`, reason `gate_exception`)
  instead of returning the upstream verdict; failing safety
  computations report unsafe (`global_safe=False`,
  `switching_safe=False`) instead of safe. The A1 error routing is
  unchanged; only the returned value hardens.
- **strict_mode has one coherent channel (F-009)**.
  `CognitiveOSConfig.strict_mode` is now wired through
  `CognitivePipeline` to the stability bootstrap and merged
  monotonically with the `ARVIS_STRICT_STABILITY` env var: either
  channel can enable the strict profile, neither can disable the
  other.
- **Audit artifacts are sealed at the commitment boundary (F-013)**.
  The stored IR of a result view is detached at hash time (rebuilt
  from the exact hashed bytes) so no upstream alias can diverge the
  payload from its hash, and `to_ir()` exports a defensive deep copy.
  Probe conclusion recorded: 69 frozen dataclasses carry mutable
  containers, but the reproducibility break happens through aliasing
  of the hashed artifact; mass container conversion deliberately
  avoided.
- **A2 complete (arvis-projection-v2)**. The seven projection legacy
  aliases on `CognitivePipelineContext` (`projection_certificate`,
  `projection_domain_valid`, `projection_margin`, `projected_state`,
  `pi_state`, `projection_view`, `projection_view_raw`) were removed
  after migrating every callsite (854 -> 792 lines): canonical writers
  write `ctx.projection.*` only, duck-typed readers adopt the
  projection-first dual pattern with a plain-attribute fallback for
  mock contexts, and the PI resolver now reads the canonical
  `ctx.projection.structured_projection` (it silently depended on the
  facade before). `FROZEN_FACADE_PROPERTIES` shrinks by exactly those
  seven names.
- `arvis/api/version.py`: the source-checkout `PACKAGE_VERSION`
  fallback, which had silently stayed at `0.1.0a2` since the a3 bump
  (an F-018 instance), now mirrors the package version again.

### Removed

- The request-facing `extra` channel for `force_tool`,
  `_force_execution`, `force_safe_projection` and
  `force_safe_switching` (F-001): no gate or runtime path reads these
  keys from `ctx.extra` anymore; replaying an old IR carrying them is
  inert by construction.
- The projection legacy alias block and its
  `TODO(arvis-projection-v2)` marker (A2).

### Notes / next

- veramem follow-ups once the pin is bumped: call
  `engine.freeze_tools()` at the end of backend bootstrap and log the
  fingerprint (ZK-safe scalar); evaluate
  `AuditCommitmentPolicy.REQUIRED` for the governed agent path (the
  effectful profile).

## [0.1.0a3] - 2026-07-15

### Added

- **Broad-except classification guard**
  (`tests/contracts/test_broad_except_guard.py`). Every broad handler in
  `arvis/` must now re-raise or build a typed error (C1), route through the
  sanctioned error machinery (C2: `ErrorManager` methods, `normalize_error`,
  the syscall failure helpers, `_attach_degraded`, the canonical boundary
  adapters of `arvis/errors/boundaries/`, `_attach_mid_trace_failure`), or
  carry a normalized `# arvis-broad: <reason>` justification marker (C3).
  The zone ratchet is closed at ceiling 0: no zone is exempt.
- **Context facade shrink ratchet**
  (`tests/contracts/test_context_facade_ratchet.py`). Freezes the 63
  compatibility properties of `CognitivePipelineContext`: new code must use
  the sub-contexts directly, and the facade can only shrink until the
  callsite migration tracked in-code as TODO(arvis-projection-v2).

### Changed

- 37 broad `except Exception` handlers narrowed to their actual failure
  contracts (numeric coercion triples/quadruples, `ImportError` on designed
  import fallbacks, `ValueError` on enum construction,
  `AttributeError`/`TypeError` on duck-typed assignment guards) across the
  api, adapters, ir, telemetry, math, stability, conversation, runtime,
  cognition, kernel_core and kernel zones.
- Around 40 deliberate fail-soft boundaries now carry the machine-checkable
  `# arvis-broad:` marker (total coercion primitives, observe-only
  telemetry, defensive view enrichment, replay boundary, the global
  stability observer, the conversation bridges, hook isolation,
  per-rule/per-entry isolation, best-effort owner resolution).

### Removed

- Five dead compatibility aliases on `CognitivePipelineContext`
  (`control_runtime`, `quadratic_lyap_snapshot`, `runtime_projection`,
  `structured_projection`, `use_paper_slow_dynamics`), each verified to
  have zero attribute access and zero string/getattr access across arvis,
  tests and compliance (898 -> 854 lines).

## [0.1.0a2] - 2026-07-09

### Removed

- Unused kernel key-value memory substrate (`kernel_core/memory/*`, `memory.*`
  syscalls, observation-long journal). No consumer, and its plaintext record
  model was off-thesis relative to the ZKCS long-term declarative memory
  (`arvis/memory/*`), which remains the memory of arvis.
  
### Added

- **Packaging and typing.** Declared `[build-system]` (setuptools +
  `setuptools.build_meta`); ship a PEP 561 `py.typed` marker so downstream type
  checkers (starting with veramem) see arvis as a typed package; expose the
  top-level `arvis.__version__`, single-sourced from the installed package
  metadata; add a CI `build` job that produces the wheel and sdist, runs
  `twine check`, asserts `py.typed` is present in the wheel, and smoke-imports
  the built wheel in a clean virtual environment. First tag-consumable release.
- Capability manifest on `ToolSpec`: declarative governance metadata so a host
  can govern sovereignty, egress and consent uniformly across local and external
  (e.g. MCP) tools. New fields: `provider` (third-party identity), `data_egress`
  (outbound data flow), `data_class` (host-defined sensitivity),
  `required_consent` (opaque consent key) and `reversible` (undo-ability), plus
  the derived `crosses_trust_boundary` property. ARVIS does not interpret the
  opaque labels; the host maps them onto its consent system, data taxonomy and
  egress policy. Defaults preserve prior tool behavior. `examples/05` extended
  to contrast a sovereign tool with a connected/egress one, and the tool docs
  (authoring guide, tool system spec) document the manifest.
- Governed input-risk gate: an explicit top-level `risk` scalar in the cognitive
  input is graded by a three-band policy (low -> ALLOW, medium ->
  REQUIRE_CONFIRMATION, high -> ABSTAIN). It supersedes the sparse-projection
  fail-closed for pure risk-scalar inputs while never relaxing a real safety
  veto (kappa / adaptive instability), and keeps the emitted IR consistent.

### Notes / next

- Unify the emitted IR version string (currently divergent across
  `arvis/api/ir.py` = `arvis-ir.v1`, `arvis/ir/version.py` = `1.0`,
  `arvis/adapters/ir/state_adapter.py` = `1.0`, and the `1.0.0` shown in
  `docs/IR.md` / `docs/ARVIS_STANDARD_V1.md`). Deferred to the IR-alignment
  track (P0.3).
- Minimal valid projection + differentiated gate (low -> ALLOW,
  medium -> REQUIRE_CONFIRMATION, high -> ABSTAIN) (P0.1 / P0.2).

## [0.1.0a1] - Unreleased

First coherence pass toward a public alpha. This release resolves versioning
and positioning inconsistencies; it does not add features.

### Changed

- **Versioning is now coherent across three explicit axes.** Package version
  `0.1.0a1`, API version `0.1`, standard version `draft-v1`.
- `pyproject.toml`: `version` set to `0.1.0a1`; classifier changed from
  `Development Status :: 4 - Beta` to `Development Status :: 3 - Alpha`.
- `arvis/api/version.py`: `API_VERSION` changed from `1.0.0` to `0.1` so the
  emitted public contract does not over-promise a stable API; the
  `PACKAGE_VERSION` source-checkout fallback now mirrors the package version
  (`0.1.0a1` instead of `0.0.0-dev`).
- `README.md`: repositioned as an honest `0.1.0-alpha` preview with a
  developer-first install path and a Known Limitations section; removed the
  "Beta" status.

### Added

- `arvis/api/version.py`: `STANDARD_VERSION` constant (`draft-v1`), exported
  from `arvis.api`.
- `CHANGELOG.md` (this file).

### Tests

- `tests/api/test_api_contract_v1.py`: version lock updated to
  `API_VERSION == "0.1"` (was `1.0.0`). The public API fingerprint is computed
  from the top-level `arvis.__all__` and is unaffected by this change.
