# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in ARVIS, please report it by email:

admin@veramem.com

Please do not open public issues for security vulnerabilities.

---

## Scope

This project focuses on:

- deterministic cognitive execution
- stability-constrained systems
- auditability and traceability
- governed external effects, authorization capabilities and intent/receipt
  integrity
- canonical commitment collisions and cross-identity tool execution

Security issues related to these areas are treated with high priority.

## Effect-boundary assumptions

ARVIS authenticates no credentials itself. A production host must stamp a real
`AuthenticatedPrincipal`, provide a qualified durable audit sink and inject
business dependencies into tools. Reports are in scope when ARVIS accepts a
cross-context capability, permits an effect without an accepted intent, exposes
a direct execution bypass, or aliases operationally distinct canonical
material.

The mutable pipeline context, credentials and live service objects must never
be transported to a tool. The complete contract is documented in
`docs/architecture/EFFECT_PATH.md`.
