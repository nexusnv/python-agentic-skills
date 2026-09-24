# Changelog

All notable changes to this project are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project uses semantic versioning.

## [Unreleased]

## [0.1.0] - 2026-09-24

### Added

- `python-blackbox-testing`, an independently installable skill for framework-agnostic black-box,
  contract, characterization, regression, and public-boundary testing workflows. It ships the
  activation description, non-negotiable rules, workflow, failure handling, and output contract
  sections, three on-demand references, and eval fixtures.
- `python-parameterized-testing`, an independently installable skill for input matrices, boundary
  cases, generated examples, properties, and replayable parameterized testing workflows, with the
  same section contract, three references, eval fixtures, and a bundled planner script.
- A standard-library-only, non-executing case planner at
  `.agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py` that plans a bounded,
  deterministic boundary-priority Cartesian matrix (or a seeded sample when `seed` and `sample_size`
  are supplied together) as JSON on stdout and rejects malformed input with exit code 2.
- skills.sh discovery and per-skill installation commands for either skill:
  `npx skills add nexusnv/python-agentic-skills --list`,
  `npx skills add nexusnv/python-agentic-skills --skill python-blackbox-testing`, and
  `npx skills add nexusnv/python-agentic-skills --skill python-parameterized-testing`. The
  `--list`, `--skill`, and `--global` flags were verified against `skills@1.7.0`, and local-path
  discovery lists both skills.
- A dated research report at
  `docs/research/2026-09-24-python-testing-skills-landscape.md` with primary sources,
  evidence-versus-inference labels, and stated limitations (install counts are deduplicated CLI
  telemetry, not unique users, successful executions, or quality signals).
- A shared safety and evidence contract in both skills covering synthetic/local-isolated defaults,
  unconditional refusal of real secrets, live credentials, customer data, and production data,
  explicit approval gates for live, destructive, and cost-incurring actions, redaction and
  untrusted-content handling, a diagnosis-only default for product code, project-native tests,
  exact commands with exit statuses, pass/fail/skip/expected-failure/not-run results, minimized
  reproducers, retained regressions, and explicit coverage gaps and not-run work.
- Framework-agnostic guidance that works with pytest, unittest, or plain Python while treating
  pytest, Hypothesis, Pact, and browser drivers as optional integrations that are never installed
  silently.
- Repository foundation: a catalog-style README, repository agent rules in `AGENTS.md`,
  `CONTRIBUTING.md`, `SECURITY.md` with private vulnerability reporting, an MIT `LICENSE`, a
  `skills.sh.json` catalog grouping, and development-only `pyproject.toml` tooling with a committed
  `uv.lock` (no build backend and no runtime package).
- Repository validation: structural, quality-contract, and case-matrix test suites (408 tests),
  positive/near-miss/safety/evidence eval fixtures for both skills, and a GitHub Actions workflow
  that runs Ruff, pytest, the official `skills-ref` validator for each skill, `skills.sh.json`
  syntax, a range-anchored whitespace check, a final worktree-cleanliness gate that fails the run
  if the checkout is left with modified or new untracked non-ignored files, and a pinned
  `skills@1.7.0` discovery smoke test.

### Verification (local, 2026-09-24)

_This subsection is a deliberate repo-specific addition beyond Keep a Changelog, per this repo's
evidence conventions._

Commands run on this checkout with their observed results:

| Command | Observed result |
| --- | --- |
| `uv run --group dev ruff check .` | exit 0, "All checks passed!" |
| `uv run --group dev ruff format --check .` | exit 0, "21 files already formatted" |
| `uv run --group dev pytest -q` | exit 0, "408 passed in 13.67s" |
| `uv run --group dev python -m json.tool skills.sh.json >/dev/null` | exit 0 |
| `uvx --python 3.11 --from 'skills-ref==0.1.1' agentskills validate .agents/skills/python-blackbox-testing` | exit 0, "Valid skill" |
| `uvx --python 3.11 --from 'skills-ref==0.1.1' agentskills validate .agents/skills/python-parameterized-testing` | exit 0, "Valid skill" |
| `uv run --group dev python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` | exit 0 |
| `git diff --check` | exit 0 |
| `npx skills@1.7.0 add . --list` | exit 0; both skill names appear as whole listing lines |

This release does not claim adoption figures, a quality ranking, or any semantic-eval pass; the
eval files are review fixtures, not executed results. The GitHub Actions workflow runs only on
GitHub and was not executed locally. The remote install path (`nexusnv/python-agentic-skills` on
GitHub) was not exercised over the network because these commits are not pushed yet; local-path
discovery was used instead.

[Unreleased]: https://github.com/nexusnv/python-agentic-skills/compare/main...HEAD
[0.1.0]: https://github.com/nexusnv/python-agentic-skills/commit/8fe2abf54ecf689adc318dc78fdc66473b32e2d8
