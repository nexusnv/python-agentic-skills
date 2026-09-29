# Heuristics and tools

Use this reference when triaging scanner output. Every pattern below is advisory; confirm
with a focused rerun, documentation comparison, or approved optional probe before raising
severity above Minor.

## Assertion patterns

- **No-assertion test:** a test function with zero assert statements and no
  `pytest.raises`, `unittest` assertion, or documented helper assertion. Often setup-only
  or accidentally empty.
- **Weak truthy check:** `assert result`, `assert data`, or `assert len(data) > 0` where
  the contract supports an exact value, schema, or error. Prefer exact equality, type,
  and message checks.
- **Mock echo:** a mock is programmed with `return_value` or `side_effect` and the test
  asserts that same value without exercising real logic. Check whether removing the
  system under test would still pass. The static scanner detects `unittest.mock`
  import-based configuration; `pytest-mock`'s `mocker` fixture style is not detected
  statically and must be confirmed by reading the test.
- **Exception ambiguity:** bare `except`, broad `except Exception`, or `pytest.raises`
  without `match=` where the contract names a message. Assert exact type and message
  fragment without volatile identifiers.
- **Snapshot without authority:** golden or snapshot comparison whose expected file was
  generated from current output and never reviewed. Label characterization until a
  documented source anchors it.

## Coupling patterns

- **Private access:** references to `_private` names, module globals, or internal state
  from tests when a public seam exists. Redirect to the public boundary.
- **Call-order lock:** `assert_called_once_with`, `call_count`, or `mock_calls` on
  internals as the primary oracle. Keep behavior assertions primary.
- **Refactor probe:** describe what internal change would break the test without changing
  the public contract. If the list is long, the test is brittle.

## Isolation patterns

- **Global mutation:** writes to `os.environ`, `sys.path`, working directory, or module
  globals without scoped teardown. Prefer `monkeypatch`, `tmp_path`, and fixtures.
- **Order risk:** shared files, databases, or singletons across tests with no reset.
  Confirm with a rerun in a different order only when the runner supports it.
- **Nondeterminism:** unseeded time, UUID, randomness, network, or locale dependence.
  Control or record the source for replay.

## Optional probes and budgets

- **Coverage report:** use the project's configured `coverage` or `pytest --cov` command
  only when already present. Inspect configuration for omitted paths and weak
  `fail-under` thresholds; do not impose a new tool silently.
- **Mutation sample:** use `mutmut`, `cosmic-ray`, or a similar tool only when already
  available or explicitly approved. Sample high-risk modules with a fixed seed, cap
  mutants and time, and report killed, survived, and not-run mutants. A survived mutant
  on a contract path confirms a Critical finding; high coverage with low kills confirms
  hollow protection.
- **Ordering probe:** use `pytest-randomly`, `pytest-xdist`, or repeated focused reruns
  only when available or approved. Record seeds, retries, and every outcome.

## False-positive control

- Quote the exact test lines that triggered the pattern and name the dimension.
- Check for helper assertions and shared fixtures before flagging no-assertion cases.
- Prefer one decisive confirmation over many heuristic matches. When confirmation is
  blocked, keep the finding Minor with confirmed set to no and record the blocker.

## Safety boundary

**Unconditionally refuse real secrets, live credentials, customer data, and production
data.** Approval may permit only a narrowly scoped, non-sensitive live call, destructive
operation, or cost-incurring action; approval never authorizes secret or data access.
