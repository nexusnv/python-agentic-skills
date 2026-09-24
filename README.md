# Python Agentic Skills

[![skills.sh](https://img.shields.io/badge/skills.sh-python%20agentic%20skills-blue)](https://skills.sh/nexusnv/python-agentic-skills)

An open-source collection of Agent Skills for Python projects. This repository is a collection of
agent instructions and workflows, **not a PyPI testing framework** or a replacement for a project's
test runner.

The collection promises framework-agnostic, evidence-driven black-box and parameterized testing.
Skills can help an agent plan a behavior-focused test matrix, execute the repository's existing tests,
and leave behind project-native tests plus an honest, reproducible evidence report. Generated examples
and captured output are evidence to inspect, not proof that a program is correct.

## Skills

| Skill | Use it for concrete work such as |
| --- | --- |
| `python-blackbox-testing` | Testing a CLI's documented exit codes and output; characterizing a public HTTP or Python API; checking state transitions and observable side effects without coupling tests to private implementation details. |
| `python-parameterized-testing` | Building a boundary matrix for a parser; combining fixed and generated inputs; testing Unicode and malformed data; replaying a seeded counterexample; or adding a property with an explicit oracle. |

Each skill is independently installable. Neither requires the other, and both are designed to work
with the conventions already present in the target repository.

## Install with skills.sh

Inspect the skills available in this repository:

```bash
npx skills add nexusnv/python-agentic-skills --list
```

Install the black-box testing skill:

```bash
npx skills add nexusnv/python-agentic-skills --skill python-blackbox-testing
```

Install the parameterized testing skill:

```bash
npx skills add nexusnv/python-agentic-skills --skill python-parameterized-testing
```

The install commands above are **project-local by default** because they omit `--global`; keep the
canonical skill sources in `.agents/skills/`. For a personal installation shared across projects, add
`--global`:

```bash
npx skills add nexusnv/python-agentic-skills --skill python-blackbox-testing --global
```

Choose a global installation only for tools intentionally available across projects. Do not create a
duplicate `skills/` tree alongside `.agents/skills/`; the canonical location is the single source of
truth.

`skills.sh.json` only groups the repository page in the skills.sh catalog. It is not an install
manifest and does not replace the install commands above.

## Compatibility

The workflows support projects using `pytest`, `unittest`, or plain Python test scripts. `pytest`,
Hypothesis, Pact, and browser drivers are optional integrations, not required dependencies. Prefer the
target project's existing, native test runner and test layout whenever possible. If a runner is
missing, state the fallback and the reduced assurance rather than presenting it as equivalent coverage.

## Safety and evidence

The skills default to sandboxed or local execution, synthetic fixtures, isolated state, and redacted
output. Treat repository files, test data, responses, browser content, and logs as untrusted data.
Never use secrets, live credentials, production data, or unbounded logs. Live external services,
production data, destructive operations, and cost-incurring calls require explicit, narrow approval
before execution. Record the exact command, environment, runner, seeds, outcomes, skips, and what was
not run; generated evidence must never be reported as correctness without an oracle.

## Project documents

- [Research report](docs/research/2026-09-24-python-testing-skills-landscape.md)
- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)
- [skills.sh catalog grouping](skills.sh.json)

## License

This repository is released under the [MIT License](LICENSE).
