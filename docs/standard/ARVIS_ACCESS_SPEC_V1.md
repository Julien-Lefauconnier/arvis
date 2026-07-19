# ARVIS Access Control Specification v1

## Status

* Version: v1
* Scope: Normative
* Component: Kernel Core, Authorization Layer
* Position: Level 5 (Execution Model), subordinate to Gate (Level 2) and IR (Level 3)

---

## 1. Purpose

This specification defines the **authorization layer** of the ARVIS kernel: the
mechanism by which the syscall boundary decides whether a given identity is
permitted to perform a given syscall on a given resource.

It realizes the obligation already stated in `ARVIS_SYSCALLS_SPEC_V1` (Security
Model): *policy-enforced authorization via kernel services*. It promotes the
"permission system" and "capability-based access control" items from that
spec's Future Extensions into a normative, versioned contract.

This layer governs **access**, not cognition. It MUST NOT influence decision
semantics, the Gate verdict, or the cognitive pipeline. It operates strictly at
the execution boundary.

---

## 2. Position in the Hierarchy

* Authorization is an **execution policy** (Level 5). It is evaluated at the
  syscall boundary, post-decision, consistent with the Execution Boundary
  Contract (no syscalls during cognition).
* Authorization MUST NOT override the Gate. A denied access surfaces as a
  normative reason code (Level 3) consistent with the Gate verdict, never as a
  silent mutation of cognition.
* Authorization MUST be deterministic and replay-safe: identical context yields
  an identical verdict, and verdicts are journaled like any syscall outcome.

---

## 3. Model

### 3.1 Principal

A `Principal` is the identity on whose behalf a syscall is executed.

    Principal:
        user_id: str
        organization_id: str | None
        grants: frozenset[str]

A bare principal (user_id only, no organization, no grants) denotes the
**resource owner**. This reproduces the pre-authorization behaviour, where
access was scoped solely by user_id.

For a production effect, a bare `Principal` is insufficient. The host MUST
stamp an `AuthenticatedPrincipal`, which extends the same owner/grant model
with non-secret governance material:

    AuthenticatedPrincipal:
        user_id: str
        organization_id: str | None
        grants: frozenset[str]
        authentication_source: str
        authentication_strength: str
        service_id: str | None
        session_id_hash: str | None

ARVIS does not validate credentials. Construction of this object is the host's
attestation that authentication already occurred.

### 3.2 AccessContext

An `AccessContext` is the triple evaluated by a policy.

    AccessContext:
        principal: Principal
        effect: SyscallEffect          # READ or EFFECT (per ARVIS_SYSCALLS_SPEC)
        resource_owner_id: str
        resource_organization_id: str | None   # owning organization, None when personal
        resource_id: str | None
        syscall_name: str | None

### 3.3 AccessDecision and AccessVerdict

    AccessDecision := ALLOW | DENY

    AccessVerdict:
        decision: AccessDecision
        reason_code: str | None        # canonical access-layer code on DENY

---

## 4. Authorization Policy Contract

An `AuthorizationPolicy` exposes a single operation:

    decide(context: AccessContext) -> AccessVerdict

Requirements (normative):

* **Deterministic**: an identical context MUST yield an identical verdict.
* **Side-effect free**: `decide` MUST NOT perform I/O or mutate state.
* **Fail-closed**: when the answer is uncertain, the policy MUST return DENY.
* On DENY, the verdict MUST carry a canonical access-layer reason code.

---

## 5. Enforcement

* Authorization is enforced at the **syscall boundary**, via a kernel service
  registered in the `KernelServiceRegistry` (per `ARVIS_KERNEL_SERVICES_SPEC`).
* The `SyscallHandler` MUST evaluate the active policy before dispatching a
  governed syscall, and MUST refuse a DENY verdict by returning a failed
  `SyscallResult` carrying an `ArvisSecurityError` (`domain = kernel.security`,
  fail-closed).
* A refused syscall MUST be journaled like any other syscall outcome (full
  observability, replay-safe).
* The absence of a configured policy MUST be treated as the default
  owner-scoped policy (Section 7), never as unconditional allow.

> Enforcement wiring in the handler is specified here but delivered as a
> distinct, behaviour-neutral increment, so that the core boundary edit is
> reviewed in isolation.

### 5.1 Identity Transport and Trust Boundary

The `Principal` is **ambient identity**, carried on the execution context and
stamped by the realization layer at the start of a run, not passed as a
per-syscall operational argument. This separates the **trusted identity
channel** (the context, set from an authenticated session) from the
**operational parameter channel** (the syscall arguments, which may be
influenced by cognition downstream of the Gate). Routing identity through the
argument channel would let a caller self-declare its own rights on every call;
routing it through the context models identity as process state, established
once at authentication.

The identity carried on the context is a **trusted input**. ARVIS does not
authenticate it and MUST NOT derive it from cognition; the authorization
guarantee of this layer is conditional on the realization layer establishing
that identity from an authenticated session. Local, test and research postures
may fall back to a bare user-scoped principal. In production, every EFFECT
syscall MUST carry an `AuthenticatedPrincipal` whose `user_id` matches the turn
owner (or the exact kernel principal for kernel-internal effects); otherwise the
syscall is refused before intent persistence and before the effect.

---

## 6. Reason Code

A new normative reason code is registered in the **access** layer:

    access_denied   (layer: access, severity: high, normative)

Per `ARVIS_REASON_CODE_REGISTRY`, a `high` normative reason code MUST force the
verdict to be not ALLOW. This guarantees that an access denial surfaces as a
governed refusal and is distinguishable in the IR from a "not found" or
"absent" outcome, which prevents information leakage through the difference
between the two.

---

## 7. Reference Policies (Implementation-Aligned)

The reference implementation provides two generic policies. Both are
**mechanisms**: neither encodes any organization-specific or domain-specific
governance. Such governance belongs to the realization layer, which composes
or injects policies on this same contract.

### 7.1 OwnerScopedAuthorization (default)

* ALLOW iff `principal.user_id == context.resource_owner_id`.
* DENY otherwise, with reason code `access_denied`.

This policy is **behaviour-neutral**: wiring it as the default reproduces the
pre-authorization access model (owner == user_id) exactly. It is the policy
assumed by Section 5 when no policy is configured.

### 7.2 OrganizationScopedAuthorization

A generic, organization-aware policy that subsumes the personal case:

* A resource with no organization (`resource_organization_id is None`) is
  owner-scoped, identical to 7.1.
* A resource that belongs to an organization is ALLOW iff the principal
  belongs to that same organization (`principal.organization_id ==
  context.resource_organization_id`) and holds the required capability (the
  capability token is a member of `principal.grants`).
* DENY otherwise, with reason code `access_denied`.

The required capability is derived from the context. The reference derivation
maps the structural effect to a capability (READ to a read capability, EFFECT
to a write capability). This derivation is **injectable**: a realization layer
MAY supply its own mapping from effect or syscall to a domain-specific
capability without modifying this layer.

### 7.3 Grants are opaque

`grants` are **opaque tokens** to this layer. ARVIS only tests membership of a
required capability in `principal.grants`. Assigning meaning to those tokens,
constructing the `Principal` (its organization and grants) from an identity
system, labelling resources with their owner and organization, and authoring
any governance beyond these reference mechanisms are responsibilities of the
realization layer. This boundary keeps the standard generic and auditable
while organization-specific governance remains private to the realization
layer.

---

## 8. Compliance

An implementation conforms to this specification if and only if:

* every governed syscall is evaluated by an authorization policy before dispatch;
* a DENY verdict fails closed with an `ArvisSecurityError` and is journaled;
* the `access_denied` reason code is emitted on denial and is consistent with
  the Gate verdict;
* policy evaluation is deterministic and replay-safe;
* the absence of a configured policy defaults to owner-scoped authorization.

---

## 9. Design Principle

> Cognition decides what is wise.
> The Gate decides what is admissible.
> Authorization decides what is permitted.

These are distinct authorities. Authorization constrains execution without ever
reshaping cognition or overriding the Gate.
