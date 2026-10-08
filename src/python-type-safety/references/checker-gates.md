# Checker gates

Use this reference when selecting a checker, configuring strictness, triaging
error codes, or reviewing cross-checker divergences.

## Checker selection

- Use the project's configured checker. If `mypy.ini`, `setup.cfg`/`pyproject.toml`
  `[tool.mypy]`, or `pyrightconfig.json` exists, that checker wins without debate.
- **Primary selection:** the primary gate is the checker wired into project
  automation — pre-commit config, CI workflow, or tox/nox sessions, in that
  order of precedence. If both checkers are automated or neither is, ask the
  user to choose and record the choice with its reason. Never silently install
  either checker; propose the install and ask first.

## Strictness levels

- **mypy baseline:** `strict = true`. If the codebase cannot take full strict yet,
  enable explicitly and record each relaxed flag as a gap: `disallow_untyped_defs`,
  `disallow_any_generics`, `warn_return_any`, `warn_unused_ignores`,
  `no_implicit_optional`, `strict_equality`.
- **pyright gate:** `typeCheckingMode = "strict"` is required. `standard` mode is
  a non-strict stepping stone only: it may be used within an explicit error
  budget with the unknown-type diagnostics (`reportUnknownParameterType`,
  `reportUnknownVariableType`, `reportUnknownMemberType`,
  `reportMissingParameterType`) enabled, and every deviation from strict is
  recorded as a gap. A zero-error `standard` run is never presented as a
  strict gate. Record the mode and every overridden diagnostic rule in the
  report.

## Fix patterns (most common codes first)

- **mypy `no-untyped-def` / pyright `reportUnknownParameterType`:** annotate the
  full signature including the return; start at the public boundary.
- **`assignment` / `reportAssignmentType`:** narrow the declared type or the value;
  do not widen the declaration to `Any` to silence it.
- **`arg-type` / `reportArgumentType`:** fix the call site or overloads; a `cast`
  at the call site needs justification.
- **`return-value` / `reportReturnType`:** make the return expression match the
  declared type; prefer narrowing over widening the declaration.
- **`attr-defined` / `reportAttributeAccessIssue`:** the attribute is genuinely
  absent on some branch — narrow first, suppression last with a code and reason.
- **`union-attr`:** guard the `None` branch explicitly; `assert x is not None`
  documents the invariant for readers and checkers alike.
- **`override`:** keep overrides compatible (accept wider, return narrower);
  LSP violations are defects, not checker pedantry.
- **`call-overload`:** add the missing overload or fix the call; never silence
  with `Any`.

## Cross-checker divergences (report, do not chase)

- mypy and pyright legitimately disagree on narrowing strictness, `strict`
  optional handling, and untyped-dependency behavior. Record each divergence with
  both checkers' exact output and move on.
- Never start a config war: do not weaken the primary checker's gate to silence
  a secondary checker's complaint.

## Plugin execution gate

- mypy plugins execute arbitrary code at check time. Before running any
  configuration that loads a plugin you have not reviewed, refuse-or-ask and
  record the block as not run, never as a pass.

## Safety boundary

**Unconditionally refuse real secrets, live credentials, customer data, and production
data.** Approval may permit only a narrowly scoped, non-sensitive live call, destructive
operation, or cost-incurring action; approval never authorizes secret or data access.
