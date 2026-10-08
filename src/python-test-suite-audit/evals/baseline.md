# Audit skill qualitative baseline notes

- **Date:** 2026-09-29
- **Run type:** Read-only design review, no live suite executed
- **Evidence class:** Authored rationale derived from the Gemini conversation and the
  approved repository design, not a controlled benchmark

The repeatable evaluation fixtures remain in `cases.yaml`.

## 1. Coverage without oracles

**Observation**

> High line coverage with weak or echoed assertions creates an illusion of quality.

**Design implication**

Require a named oracle per finding, cap unconfirmed static patterns at Minor, and demand
execution confirmation before Critical severity.

## 2. Mock and coupling traps

**Observation**

> Over-mocked tests and private call-order locks pass while proving little and break on
> safe refactors.

**Design implication**

Check mock echoes and private coupling explicitly, redirect remediation to the public
boundary, and keep the audit read-only with a separate-approval gate for any code change.

## 3. Optional deep probes

**Observation**

> Full mutation and ordering campaigns are valuable but slow, flaky, and tool-specific.

**Design implication**

Default to a quick static-only profile with budgets. Treat mutation, randomized order,
and multi-version checks as approved, sampled, opt-in tactics with recorded seeds,
truncation, and not-run work.
