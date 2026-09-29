# Audit dimensions

Use this reference to scope the audit, assign severity, and choose the profile before
inspecting tests. Static patterns alone never prove a defect; severity above Minor
requires execution confirmation or independent review.

## The six dimensions

1. **Executability and reproducibility:** collection succeeds, baseline runs on the
   project-native command, coverage configuration measures what it claims, and the CI
   command matches local execution.
2. **Assertion rigor and tautologies:** each test checks a specific behavior with a named
   oracle. Flag tests with no assertions, truthy-only checks where exact values are
   known, mock-return echoes, and baselines copied from unreviewed output.
3. **Behavioral coupling:** tests assert public contracts, not private helpers, call
   order, or internal state. Ask: would a pure internal refactor without contract change
   break this test? If yes, it locks implementation rather than behavior.
4. **Error and edge depth:** malformed, empty, boundary, Unicode, and invalid inputs map
   to documented errors with exact type and message checks plus no-mutation guarantees.
5. **Isolation and determinism:** tests run in any order, clean up files, environment,
   and global state, and control clocks, randomness, network, and filesystem reliance.
6. **Maintainability:** duplicated logic is parametrized, fixtures are scoped, skips are
   justified, doctests execute, and lint and type checks cover the test tree.

## Severity rubric

- **Critical:** confirmed hollow protection. Examples: a test that passes regardless of
  implementation, a surviving sampled mutant on a contract path, or an asserted mock
  configuration presented as behavior coverage. Requires confirmation.
- **Major:** probable gap or brittleness. Examples: missing error-path coverage, weak
  oracle where an exact value is known, order-dependent state leak, or tight private
  coupling on a public contract.
- **Minor:** hygiene or advisory signal. Examples: unconfirmed heuristic, duplicated
  structure worth parametrizing, oversized fixture, unjustified skip, or style gap.

Cap any unconfirmed static pattern at Minor and set confirmed to no. Promote only after
a focused rerun, sampled mutation kill, ordering probe, or reviewed documentation
comparison.

## Profiles and budgets

- **Quick (default):** inventory plus executability gate plus bounded static scan. No
  mutation, no ordering rerun, no multi-version check. Suitable for most reviews.
- **Deep (opt-in):** adds sampled mutation on high-risk modules, one randomized-order
  rerun when the runner supports it, and coverage-report inspection. Each probe needs an
  explicit budget: maximum files, findings, mutants, time, and cost. Record the budget,
  the sample seed, what ran, and what was truncated or not run.

## Safety boundary

**Unconditionally refuse real secrets, live credentials, customer data, and production
data.** Approval may permit only a narrowly scoped, non-sensitive live call, destructive
operation, or cost-incurring action; approval never authorizes secret or data access.
Prefer synthetic local execution and record blocked work as not run.
