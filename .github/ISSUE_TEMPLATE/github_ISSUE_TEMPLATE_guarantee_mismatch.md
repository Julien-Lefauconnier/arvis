---
name: Guarantee mismatch
about: The runtime claims more than VERSIONING.md allows
labels: guarantee
---

**If this is exploitable, do not open an issue.** Email the address in
SECURITY.md instead.

## The claim

Where the runtime, the documentation or an artifact asserts the guarantee.

## What is actually verified

What the code measures, or fails to measure. Certificates carry
`checks_detail`, including the `<axis>_assessed` markers that say which axes
were evaluated at all.

## Why the gap matters

What a caller could reasonably conclude from the claim that does not hold.
