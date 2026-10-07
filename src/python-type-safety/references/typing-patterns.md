# Typing patterns

Use this reference when choosing annotations. Every pattern is advisory until a
checker run confirms it. Never suggest syntax newer than the project's
`requires-python`; check the floor first (`X | Y` needs 3.10, `TypeAlias`
needs 3.10, `ParamSpec` needs 3.10, `match` narrowing needs 3.10).

## Precision patterns

- **Exact over `Any`:** annotate the narrowest true type. Every `Any` needs a
  justification recorded in the report; unreviewed `Any` is an advisory finding.
- **Optionals:** `str | None` (3.10+) or `Optional[str]` below the floor. Never
  use a bare `None` default without the `Optional` marker.
- **Collections:** parameterize builtins (`list[int]`, `dict[str, Report]`) at or
  above the floor; use `typing.List` forms only below 3.9.
- **Protocols over ABCs:** prefer `typing.Protocol` for structural interfaces;
  reserve ABCs for shared implementation. Keep protocols small and single-purpose.

## Generics and overloads

- **TypeVars:** bind with `bound=` where the contract names one; avoid
  unbounded `TypeVar` on public boundaries.
- **Overloads:** use `@overload` only when one signature cannot express the
  boundary; keep the implementation signature compatible with every overload.
- **TypedDict and dataclasses:** prefer `TypedDict` for fixed-shape mappings
  and frozen dataclasses for value objects; total=False only with justification.

## Narrowing and exhaustiveness

- **Narrow with `assert` or `isinstance`:** never silence a narrowing error with
  `cast` when an assertion expresses the invariant.
- **`Never` and `NoReturn`:** mark exhaustive branches and never-returning
  helpers so the checker verifies exhaustiveness.
- **No untyped defs:** every function needs full annotations including the
  return type; `__init__` needs `-> None`.

## Suppression hygiene

- **Coded ignores only:** `# type: ignore[code]` with a reason comment. Bare
  `# type: ignore` is an advisory finding.
- **`warn_unused_ignores` on:** stale suppressions must fail loudly. Remove the
  suppression instead of widening the ignore when the error disappears.

## Safety boundary

**Unconditionally refuse real secrets, live credentials, customer data, and production
data.** Approval may permit only a narrowly scoped, non-sensitive live call, destructive
operation, or cost-incurring action; approval never authorizes secret or data access.
