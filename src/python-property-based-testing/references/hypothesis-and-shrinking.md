# Hypothesis and shrinking

Use this reference after the property, domain, oracle, and project runner are
known. Strategies and shrinking are evidence aids; they never replace a
meaningful property or a project-native test.

## Hypothesis setup recipe

1. Confirm Hypothesis is already installed or get explicit approval to add it
   as a development dependency. Never install it silently. Record the
   installed version because settings, strategies, and failure output vary by
   version.
2. Keep the project's runner and existing fixtures as the primary integration
   point. A `@given` test lives beside the project's pytest, unittest, or
   plain-Python tests; do not impose a new runner.
3. Configure `settings` explicitly: `max_examples`, `deadline` (use `None`
   only with a stated time budget elsewhere), `derandomize` for replay, and
   the `database` directory for example persistence. Record every setting in
   the evidence report.
4. Define one Hypothesis profile per budget (for example a quick local profile
   and a longer nightly profile) and record which profile ran.

## Deterministic generation recipe

1. Write the strategy sketch from the properties reference, then implement it
   with bounded base strategies and small reviewed composites.
2. Choose a seed that is recorded in the report and test. With Hypothesis, use
   `derandomize=True` plus the failing example's explicit replay; without
   Hypothesis, use a local generator such as `random.Random(seed)` rather
   than global random state.
3. Derive each case from a stable case ID or index so adding unrelated cases
   does not change a witness unexpectedly. Make collection ordering,
   serialization, and fixture names stable.
4. Bound count, time, input size, memory, request rate, and cost before
   generation. Stratify across families rather than letting one common family
   consume the budget.
5. Record the seed, Hypothesis version and settings, normalization, discarded
   count, assume-filtered count, truncated flag, and exact replay command. Two
   runs with the same recorded state should produce the same witnesses.

The bundled `scripts/plan_property_matrix.py` plans an explicit property and
strategy matrix from stated properties, dimensions, and boundary values. When
`seed` and `sample_size` are supplied together it produces a deterministic
seeded sample. It is still a planner and never executes the target project.

## Normalization and nondeterminism

- Control or inject clocks and record timezone, locale, and time format.
- Control or inject UUIDs and other identifiers; never rely on ambient
  randomness in a replay.
- For Unicode or whitespace properties, record
  `unicodedata.unidata_version` or an explicitly fixed whitespace character
  set so replay does not depend on an unrecorded runtime.
- Record relevant environment variables, process settings, and dependency
  versions without secrets.
- Normalize unordered output only where order is not part of the oracle. State
  each normalization and why it is safe.
- Isolate state, files, databases, caches, and network endpoints between
  witnesses. Reset or model state explicitly; do not let a prior generated
  case hide a later failure.

## Fallback without Hypothesis

For a project without Hypothesis, use a deterministic table plus a bounded
seeded generator. The fallback must disclose that it has reduced coverage, no
automatic shrinking, and a finite witness count. A unittest or plain-Python
test remains valid; do not impose pytest just to add generated cases.
Minimize manually with a binary-search pattern: halve the input, replay, and
keep the smaller input only while the same failure and oracle persist; record
each kept and discarded reduction attempt.

## Shrinking and minimization

- On failure, preserve the original generated input, seed, Hypothesis
  settings, environment, state, command, and failure.
- Replay the original failure before attempting a smaller case.
- With Hypothesis, let the shrinker run to completion and record the shrunken
  input, the shrinking method, and the number of shrunk steps.
- Reduce the input while checking that the same meaningful failure and oracle
  remain observable. Remove unnecessary fields, values, collection elements,
  operations, and state transitions.
- Record the minimized input, the minimization method, discarded attempts,
  and whether the result is a product defect, bad oracle, environment issue,
  or flake.
- Retain the original failure record, the minimized reproducer, and a fixed
  regression when stable; retain the broader property when practical.
- Do not delete retries, skipped cases, or failed attempts to make the final
  result look clean.

## Filtering and early-return anti-patterns

Do not return before asserting an invalid case's documented error and
no-mutation guarantee. Do not use `assume` to filter out hard values, unusual
Unicode, large collections, or exceptions merely because they make the suite
inconvenient. If a precondition is necessary, isolate it, record the
assume-filtered case and reason, and report the resulting coverage impact.
Prefer explicit domain labels over silent filtering. Excessive rejection rates
are a strategy-design defect, not a passing result.

## Budgets

Set limits for case count, wall time, input size, memory, request rate, retry
count, and monetary cost. A bounded helper or project-native test must stop
before an unbounded product, report truncation, and disclose which families
were not sampled. **Unconditionally refuse real secrets, live credentials,
customer data, and production data.** Approval may permit only a narrowly
scoped, non-sensitive live call, destructive operation, or cost-incurring
action; approval never authorizes secret or data access. Use synthetic data
and isolated dependencies; bound and redact all evidence.

## Stateful sequences

Stateful `RuleBasedStateMachine` testing is out of scope for v1. When
operation order or interleaved sequences are the actual risk, record the
property as not-run with the reason `stateful sequences deferred`, describe
the sequence risk and the isolation such a test would need, and stop. Do not
build an ad-hoc stateful harness as a substitute.
