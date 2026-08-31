---
name: Feature request
about: Propose a capability for the kernel
labels: enhancement
---

## The problem

What cannot be done today, and what you had to do instead.

## Why it belongs in the kernel

ARVIS carries the generic mechanism; the layer built on it carries the meaning.
A capability that must know what a domain means (a vocabulary, a template, a
renderer, a heuristic reading intent from language) belongs in that layer, not
here. See the boundary section in CONTRIBUTING.md.

Explain what makes this generic.

## What it would touch

Public API, effect path, canonical bytes, or none of these. Anything that
changes canonical bytes changes a format version and invalidates old hashes.
