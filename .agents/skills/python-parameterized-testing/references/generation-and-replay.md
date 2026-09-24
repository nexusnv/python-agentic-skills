# Generation and replay

Use this reference after the domain, property, oracle, and project runner are known. Generation is
an evidence aid; it never replaces a meaningful property or a project-native test.

## Deterministic generation recipe

1. Select a project-native fixed-example table and identify the valid, invalid, and unsupported
   input families.
2. Choose a seed that is recorded in the report and test fixture. Use a local generator such as
   `random.Random(seed)` or the project’s existing deterministic generator rather than global random
   state.
3. Derive each case from a stable case ID or index so adding unrelated cases does not change a
   witness unexpectedly. Make collection ordering, serialization, and fixture names stable.
4. Bound count, time, input size, memory, request rate, and cost before generation. Stratify across
   families rather than letting one common family consume the budget.
5. Record the seed, generator and version, normalization, discarded count, truncated flag, and
   exact replay command. Two runs with the same recorded state should produce the same witnesses.

The bundled `scripts/plan_case_matrix.py` only plans an explicit boundary-priority Cartesian
matrix. It rejects `seed` and `sample_size`; use it when values are explicit, and use the target
project’s seeded generator or an approved property library for sampled generation.

## Normalization and nondeterminism

- Control or inject clocks and record timezone, locale, and time format.
- Control or inject UUIDs and other identifiers; never rely on ambient randomness in a replay.
- Record relevant environment variables, process settings, and dependency versions without secrets.
- Normalize unordered output only where order is not part of the oracle. State each normalization
  and why it is safe.
- Isolate state, files, databases, caches, and network endpoints between witnesses. Reset or model
  state explicitly; do not let a prior generated case hide a later failure.

## Hypothesis and project-native fallbacks

Hypothesis is an optional tactic, not a dependency to install silently. Use it only when already
available or explicitly approved, and record the installed version because APIs, settings, and
failure output can vary by version. Keep the project’s runner and existing fixtures as the primary
integration point.

For a project without Hypothesis, use a deterministic table plus a bounded seeded generator. The
fallback must disclose that it has reduced coverage, no automatic shrinking, and a finite witness
count. A unittest or plain-Python test remains valid; do not impose pytest just to add generated
cases.

## Shrinking and minimization

- On failure, preserve the original generated input, seed, environment, state, command, and failure.
- Replay the original failure before attempting a smaller case.
- Reduce the input while checking that the same meaningful failure and oracle remain observable.
  Remove unnecessary fields, values, collection elements, operations, and state transitions.
- Record the minimized input, the minimization method, discarded attempts, and whether the result
  is a product defect, bad oracle, environment issue, or flake.
- Retain both the original failure record and the minimized reproducer. Promote the minimized input
  to a fixed regression when stable, and retain the broader property or matrix when practical.
- Do not delete retries, skipped cases, or failed attempts to make the final result look clean.

## Filtering and early-return anti-patterns

Do not return before asserting an invalid case’s documented error and no-mutation guarantee. Do not
filter out hard values, unusual Unicode, large collections, or exceptions merely because they make
the suite inconvenient. If a precondition is necessary, isolate it, record the discarded case and
reason, and report the resulting coverage impact. Prefer explicit domain labels over silent
filtering.

## Budgets and stateful sequences

Set limits for case count, wall time, input size, memory, request rate, retry count, and monetary
cost. A bounded helper or project-native test must stop before an unbounded product, report
truncation, and disclose which families were not sampled. Approval is required for live, costly, or
destructive execution; prefer synthetic local alternatives.

Use stateful or operation-sequence testing only when sequence history is the actual risk, such as
ordering, retries, cancellation, or state transitions. Then model the sequence explicitly, reset
state, record the transition oracle, and keep the finite trace replayable. Do not add stateful
complexity to a pure function without a concrete sequence failure mode.
