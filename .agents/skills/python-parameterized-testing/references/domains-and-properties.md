# Domains and properties

Use this reference to turn a public behavior into a broad, explicit input matrix and a meaningful
oracle. Do not start generation until the domain, property, and evidence boundary are written.

## Fixed examples, generated examples, and properties

- A **fixed example** is a curated input retained permanently for a boundary, regression, or
  readable contract case. Keep empty, minimum, maximum, malformed, Unicode, and dependent examples
  when relevant.
- A **generated example** is a bounded witness selected by a generator. It expands exploration and
  can expose a failure, but it is not a quantified property and does not establish proof.
- A **property** is a quantified statement over a stated domain, such as
  `for every valid x, decode(encode(x)) == x`. State its domain, assumptions, oracle, and
  normalization before generating witnesses.

Keep a fixed regression for a reproducible failure and retain the broader property or matrix when
it remains useful. A random loop with no quantified relationship is finite randomized exploration,
not property-based proof.

## Domain classes

Separate these classes in the plan and report:

- **Valid domain:** inputs the public contract accepts and for which the property is claimed.
- **Invalid domain:** well-formed or malformed inputs that must be rejected with a documented
  stable error. Assert both rejection and absence of unintended mutation.
- **Unsupported domain:** inputs outside the supported format, version, platform, or feature set.
  Do not silently classify these as ordinary invalid cases.
- **Environment-dependent domain:** inputs or expectations that vary by clock, locale, timezone,
  filesystem, network, platform, or external state. Control or isolate the dependency and record the
  environment.

State exclusions explicitly. A focused request may narrow coverage, but it must not erase valid,
invalid, unsupported, or safety cases that are relevant to the stated contract.

## Safety boundary

**Unconditionally refuse real secrets, live credentials, customer data, and production data.**
Approval may permit only a narrowly scoped, non-sensitive live call, destructive operation, or
cost-incurring action; approval never authorizes secret or data access. Prefer a local synthetic
adapter with synthetic data and record blocked work as not run.

## Property families

Choose only properties that express meaningful behavior for the target:

- **Round-trip:** `decode(encode(x)) == x` or an equivalent inverse relationship.
- **Differential:** the target agrees with an independent reference implementation or reviewed
  model, including edge and invalid inputs.
- **Invariant:** a state or output relationship holds before and after the operation, such as
  conservation, uniqueness, or a complete mapping.
- **Idempotence:** applying the same operation twice has the same observable result as once.
- **Order:** reversing, sorting, or permuting inputs changes output only in a documented way.
- **No-crash:** the call returns or raises an allowed error for every generated witness. Treat
  this as a weak safety property, never as proof of semantic correctness.
- **State-transition:** a public operation moves state only through documented states and preserves
  the required snapshot or version invariant.
- **Metamorphic:** a documented relation connects a transformed input to a transformed output,
  such as scaling a value and scaling its expected result.

Prefer a property with an independent oracle. A property that merely repeats the implementation
is not meaningful evidence.

## Boundary families

Cover relevant boundaries rather than assuming all values are equivalent:

- empty, singleton, minimum, maximum, just below, exact boundary, and just above;
- negative, zero, sign, fractional, precision, rounding, and overflow values where relevant;
- empty, singleton, ordered, duplicated, nested, and maximum-size collections;
- empty, whitespace, combining marks, normalization forms, control characters, emoji, and
  non-UTF-8 or malformed encoding data;
- dependent values such as a name containing its identifier, a range whose endpoints depend on
  configuration, or a payload that must agree with a checksum;
- malformed syntax, missing required fields, wrong types, unsupported versions, and conflicting
  options.

Name why each selected boundary matters to the public contract. Avoid an uncontrolled Cartesian
product; stratify or cap it and report what was not generated.

## Oracle quality rules

Give every case or property a named oracle. Prefer, in order of strength when appropriate:

1. exact output, type, value, or stable documented error;
2. observable state transition or exact before/after snapshot;
3. independent differential or metamorphic relation;
4. contract matcher, schema, or reviewed golden result.

For invalid and unsupported inputs, check the documented error and absence of mutation. For
reproducibility, record normalization for genuinely volatile fields such as timestamps, UUIDs,
unordered output, or locale-specific formatting; do not normalize away meaningful differences.

A captured current result is characterization evidence unless a documented or reviewed source makes
it a contract. A finite generated sample is a witness, not proof. State assumptions, known
limitations, and coverage gaps in the evidence report.
