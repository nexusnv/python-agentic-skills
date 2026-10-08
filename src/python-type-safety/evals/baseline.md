# Type-safety skill qualitative baseline notes

- **Date:** 2026-10-07
- **Run type:** Read-only design review, no live codebase gated
- **Evidence class:** Authored rationale derived from the skills.sh registry probe
  (2026-10-07) and the approved design spec, not a controlled benchmark

The repeatable evaluation fixtures remain in `cases.yaml`.

## 1. Gradual typing without gates

**Observation**

> Partially annotated code with a non-strict checker creates an illusion of safety.

**Design implication**

Measure annotation coverage first, annotate the public boundary first, and demand a
project-native checker run before claiming typed code.

## 2. Any-silencing and suppression traps

**Observation**

> Blanket `Any` annotations and bare `type: ignore` comments silence the checker
> while proving nothing and hiding real defects.

**Design implication**

Require justification for every `Any`, a specific error code for every suppression,
and `warn_unused_ignores` so stale suppressions fail loudly.

## 3. Plugin execution risk

**Observation**

> mypy plugins execute arbitrary code at check time, so a checker run is not a
> side-effect-free read.

**Design implication**

Gate unknown plugins with refuse-or-ask before running; record the block as not run,
never as a pass.
