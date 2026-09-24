# Initial Python Testing Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an installable Agent Skills collection containing high-quality, framework-agnostic `python-blackbox-testing` and `python-parameterized-testing` skills, plus the research and community foundation needed for skills.sh adoption.

**Architecture:** Keep one canonical skill tree under `.agents/skills/`, with each skill independently installable. Keep `SKILL.md` concise and operational, move detailed guidance into per-skill references, and ship only one standard-library-only deterministic case-matrix helper. Use development-only Python tooling and tests to validate the Agent Skills structure, quality contracts, links, and helper behavior.

**Tech Stack:** Agent Skills specification, skills.sh, Markdown, YAML/JSON, Python 3.10+, standard library, pytest, Ruff, PyYAML, GitHub Actions, `skills-ref`.

---

## File map

The implementation creates or updates these focused units:

- `.agents/skills/python-blackbox-testing/SKILL.md` — activation contract and executable black-box workflow.
- `.agents/skills/python-blackbox-testing/references/*.md` — boundary/oracle, adapter/safety, and evidence details.
- `.agents/skills/python-blackbox-testing/evals/cases.yaml` — semantic eval fixtures for trigger and safety behavior.
- `.agents/skills/python-parameterized-testing/SKILL.md` — activation contract and executable parameterized/property workflow.
- `.agents/skills/python-parameterized-testing/references/*.md` — domain/property, generation/replay, and evidence details.
- `.agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py` — deterministic, non-executing case-matrix planner.
- `.agents/skills/python-parameterized-testing/evals/cases.yaml` — semantic eval fixtures for domains, replay, and safety.
- `tests/test_skill_structure.py` — Agent Skills format, links, size, and portable-frontmatter checks.
- `tests/test_quality_contracts.py` — required workflow, safety, and eval-fixture contracts.
- `tests/test_case_matrix.py` — helper behavior and safety tests.
- `pyproject.toml` — development-only tool configuration; no runtime package.
- `README.md`, `AGENTS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `skills.sh.json` — adoption and contributor-facing files.
- `docs/research/2026-09-24-python-testing-skills-landscape.md` — dated, cited research and adoption-factor analysis.
- `.github/workflows/ci.yml` — format, tests, skill validation, and install smoke test.

### Task 1: Add the research report

**Files:**
- Create: `docs/research/2026-09-24-python-testing-skills-landscape.md`

- [ ] **Step 1: Write the report with a dated evidence header**

Start the file with:

```markdown
# Python Testing Skills Landscape

Date: 2026-09-24
Scope: skills.sh packaging, adoption signals, and primary-source Python testing guidance
Evidence basis: skills.sh public pages and official repositories; Agent Skills, Python, pytest, Hypothesis, and Pact documentation

> Install counts are deduplicated CLI telemetry, not unique users or successful executions. Repository-level GitHub metrics are secondary signals and do not isolate adoption of an individual skill.
```

Then add sections for:

1. `## Executive summary` with the five evidence-backed design factors used by this repository.
2. `## Packaging and compatibility` with the skills.sh commands, `.agents/skills` decision, and client discovery caveat.
3. `## Adoption snapshot` with the dated table from the design spec and links to each skills.sh detail page.
4. `## What popular skills do differently` distinguishing evidence from inference, including sharp triggers, executable loops, hard gates, inspectable artifacts, progressive disclosure, and fast feedback.
5. `## Security lessons` covering secret redaction, untrusted response content, argument-safe subprocesses, and the fact that popularity is not a security signal.
6. `## Python testing guidance` covering public boundaries, oracles, isolation, negative cases, properties, replay, shrinking, and honest fallback behavior.
7. `## Design implications` mapping each finding to a concrete choice in the two skills.
8. `## References` with the primary URLs and access date.

- [ ] **Step 2: Verify the report has no unsupported certainty or placeholders**

Run:

```bash
rg -n 'TODO|TBD|always|caused|guarantees|best skill' docs/research/2026-09-24-python-testing-skills-landscape.md
```

Expected: no unqualified “caused”, “guarantees”, or “best skill” claims; the report should say “likely”, “associated with”, or otherwise qualify inference.

- [ ] **Step 3: Commit the research artifact**

```bash
git add docs/research/2026-09-24-python-testing-skills-landscape.md
git commit -m "docs: research python testing skill adoption factors"
```

### Task 2: Add the repository foundation and contributor documentation

**Files:**
- Modify: `README.md`
- Create: `AGENTS.md`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CHANGELOG.md`
- Create: `skills.sh.json`
- Create: `pyproject.toml`

- [ ] **Step 1: Write the root development configuration**

Create `pyproject.toml` with development-only configuration:

```toml
[dependency-groups]
dev = [
  "pytest>=8.3,<9",
  "pyyaml>=6.0,<7",
  "ruff>=0.9,<1",
]

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

Do not add a build backend or runtime project metadata. The README must state that this repository is installed through skills.sh, not installed as a PyPI package.

- [ ] **Step 2: Replace the placeholder README with the catalog and install contract**

`README.md` must include:

````markdown
# Python Agentic Skills

Open-source, agentic coding skills for Python projects.

This repository is a skills collection, not a PyPI testing framework. Its skills are installed with skills.sh and work with existing project test runners.

## Skills

### python-blackbox-testing

Use when you need to discover, characterize, specify, or protect Python behavior through a public API, CLI, HTTP/RPC boundary, service, file/database boundary, event, or user workflow. It creates a scenario matrix, names an oracle, executes the project-native test command, isolates side effects, and leaves project-native tests plus an evidence report.

### python-parameterized-testing

Use when you need table-driven tests, edge-case matrices, generated inputs, property-based tests, round-trip/invariant checks, or reproducible seed-based exploration. It separates properties from examples, bounds generation, supports Hypothesis as an optional tactic, and preserves minimized counterexamples.

## Install

```bash
npx skills add nexusnv/python-agentic-skills --list
npx skills add nexusnv/python-agentic-skills --skill python-blackbox-testing
npx skills add nexusnv/python-agentic-skills --skill python-parameterized-testing
```

Install globally with the CLI’s `--global` option or target a project directory by omitting it. The canonical source is `.agents/skills/`; do not copy the skills into a second `skills/` tree.

## Compatibility

- Skills: portable Agent Skills format with skills.sh discovery.
- Python: skills can guide projects using pytest, unittest, or plain Python; no framework is required.
- Optional tools: pytest, Hypothesis, Pact, browser drivers, and project-specific adapters are used only when already available or explicitly approved.
- Safety: local/sandboxed execution, synthetic data, redaction, and explicit approval for live or destructive calls are required.

## Research and contribution

- [Research](../../research/2026-09-24-python-testing-skills-landscape.md)
- [Contributing](../../CONTRIBUTING.md)
- [Security](../../SECURITY.md)
- [Changelog](../../CHANGELOG.md)
````

- [ ] **Step 3: Add repository-specific agent rules**

`AGENTS.md` must require agents to:

- read the design spec before changing skill behavior;
- keep each `SKILL.md` concise and operational;
- add or update eval fixtures for trigger, near-miss, and safety changes;
- use project-native tests and the existing runner;
- run the helper and structural test suites before completion;
- never commit secrets, live credentials, production data, or unbounded logs;
- distinguish framework-agnostic guidance from optional pytest/Hypothesis tactics.

- [ ] **Step 4: Add contribution, security, changelog, and catalog files**

`CONTRIBUTING.md` must document naming, frontmatter, progressive disclosure, references, evals, tests, and review. `SECURITY.md` must direct reports to GitHub private vulnerability reporting and warn that skills can cause command execution and process untrusted content. `CHANGELOG.md` must start with `0.1.0` and list the two skills. `skills.sh.json` must use the current display-only schema:

```json
{
  "$schema": "https://skills.sh/schemas/skills.sh.schema.json",
  "notGrouped": "bottom",
  "groupings": [
    {
      "title": "Testing",
      "description": "Framework-agnostic testing workflows for Python projects.",
      "skills": ["python-blackbox-testing", "python-parameterized-testing"]
    }
  ]
}
```

This file changes the skills.sh repository page only; it is not an install manifest or registration mechanism.

- [ ] **Step 5: Run formatting and documentation sanity checks**

Run:

```bash
python -m json.tool skills.sh.json >/dev/null
rg -n 'placeholder|TODO|TBD|not implemented' README.md AGENTS.md CONTRIBUTING.md SECURITY.md CHANGELOG.md
```

Expected: valid JSON and no placeholders.

- [ ] **Step 6: Commit the repository foundation**

```bash
git add README.md AGENTS.md CONTRIBUTING.md SECURITY.md CHANGELOG.md skills.sh.json pyproject.toml
git commit -m "docs: establish skills collection foundation"
```

### Task 3: Add the black-box testing skill

**Files:**
- Create: `.agents/skills/python-blackbox-testing/SKILL.md`
- Create: `.agents/skills/python-blackbox-testing/references/boundaries-and-oracles.md`
- Create: `.agents/skills/python-blackbox-testing/references/adapters-and-safety.md`
- Create: `.agents/skills/python-blackbox-testing/references/evidence-report.md`
- Create: `.agents/skills/python-blackbox-testing/evals/cases.yaml`

- [ ] **Step 1: Write the portable frontmatter and activation contract**

Start `SKILL.md` with:

```markdown
---
name: python-blackbox-testing
description: >-
  Discover, characterize, specify, and protect Python behavior through public
  interfaces such as APIs, CLIs, services, events, files, databases, and user
  workflows. Use when a user asks for black-box testing, contract testing,
  characterization tests, regression coverage, public-boundary tests, or
  behavior-focused verification across a Python project. Do not replace a
  public-boundary test with private implementation assertions when a public
  contract exists.
license: MIT
compatibility: Python project-agnostic; uses existing project test tools and
  does not require pytest or Hypothesis.
metadata:
  author: Nexus Envision Sdn Bhd
  version: "0.1.0"
---
```

The body must use imperative instructions and include these exact sections:

- `# Python black-box testing`
- `## Non-negotiable rules`
- `## Workflow`
- `## Failure handling`
- `## Output contract`
- `## References`

The workflow must instruct the agent to inventory public surfaces, build a broad scenario matrix, label contract/characterization/regression behavior, select an oracle, choose the lowest useful boundary, use the project-native runner, isolate state, ask before live/destructive actions, execute, minimize failures, retain regressions, and stop before product-code changes unless requested.

- [ ] **Step 2: Add detailed boundary and oracle guidance**

`boundaries-and-oracles.md` must define public versus private boundaries, contract versus characterization versus regression tests, oracle types, consumer adapters, and a scenario matrix schema with fields for input class, preconditions, expected result, expected failure, side effects, cleanup, and traceability.

- [ ] **Step 3: Add adapter and safety guidance**

`adapters-and-safety.md` must cover Python APIs, CLI subprocesses, HTTP/RPC, filesystem/database, events, and UI; it must require argument arrays, explicit environments/timeouts, temporary state, local/sandboxed dependencies, synthetic data, redaction, and explicit approval for live services or destructive actions.

- [ ] **Step 4: Add the evidence template**

`evidence-report.md` must provide a Markdown template containing boundary, consumer, runner, environment, cases, oracle, normalization, exact commands, exit status, pass/fail/skip/not-run results, failures, minimized reproducers, retained regressions, and coverage gaps.

- [ ] **Step 5: Add black-box eval fixtures**

`cases.yaml` must be a list of fixtures with `id`, `prompt`, `kind`, and `expected`. It must include positive activation, near-miss, framework-agnostic, safety, and evidence cases. The expected fields must be concrete strings or booleans, including `requires_approval: true` for live/destructive behavior and `must_not_modify_product_code: true` for the diagnosis-only default.

- [ ] **Step 6: Validate the skill structure manually**

Run:

```bash
wc -l .agents/skills/python-blackbox-testing/SKILL.md
rg -n 'public|oracle|synthetic|approval|product code|not run' .agents/skills/python-blackbox-testing
```

Expected: the core skill is below the 500-line guidance, and all safety/evidence terms are present.

- [ ] **Step 7: Commit the black-box skill**

```bash
git add .agents/skills/python-blackbox-testing
 git commit -m "feat: add python black-box testing skill"
```

### Task 4: Add the parameterized testing skill and helper

**Files:**
- Create: `.agents/skills/python-parameterized-testing/SKILL.md`
- Create: `.agents/skills/python-parameterized-testing/references/domains-and-properties.md`
- Create: `.agents/skills/python-parameterized-testing/references/generation-and-replay.md`
- Create: `.agents/skills/python-parameterized-testing/references/evidence-report.md`
- Create: `.agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py`
- Create: `.agents/skills/python-parameterized-testing/evals/cases.yaml`
- Create: `tests/test_case_matrix.py`

- [ ] **Step 1: Write the helper test before the helper implementation**

Create `tests/test_case_matrix.py` with tests that define the helper’s contract:

```python
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / ".agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py"


def run_helper(payload):
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )


def test_plan_case_matrix_is_deterministic_and_respects_limit():
    payload = {
        "dimensions": {
            "n": {"values": [0, 1, 10], "boundary": [0, 10]},
            "text": {"values": ["", "a"], "boundary": [""]},
        },
        "max_cases": 4,
    }
    first = run_helper(payload)
    second = run_helper(payload)
    assert first.stdout == second.stdout
    result = json.loads(first.stdout)
    assert len(result["cases"]) <= 4
    assert result["truncated"] is True


def test_plan_case_matrix_rejects_malformed_input():
    with pytest.raises(subprocess.CalledProcessError):
        run_helper({"dimensions": {"n": {"values": []}}, "max_cases": 0})
```

Add these concrete tests before implementing the helper:

```python
def test_plan_case_matrix_help():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "usage:" in result.stdout.lower()


def test_plan_case_matrix_preserves_explicit_boundaries():
    payload = {
        "dimensions": {
            "n": {"values": [3], "boundary": [0, 4]},
        },
        "max_cases": 3,
    }
    result = json.loads(run_helper(payload).stdout)
    assert result["cases"] == [
        {"n": 0},
        {"n": 4},
        {"n": 3},
    ]


def test_helper_has_no_execution_or_network_imports():
    source = SCRIPT.read_text()
    assert "import subprocess" not in source
    assert "import requests" not in source
    assert "from my_project" not in source
```

The helper must be non-executing and deterministic.

- [ ] **Step 2: Implement the standard-library case planner**

Implement `plan_case_matrix.py` with:

- `argparse.ArgumentParser` and `--help`;
- `json.load` from stdin;
- validation that `dimensions` is a non-empty object, each dimension has non-empty `values`, and `max_cases` is a positive integer;
- deterministic priority ordering: explicit `boundary` values first, then declared `values`, then a deterministic seeded sample only if a `seed` and `sample_size` are provided;
- Cartesian-product planning with an early cap so it never materializes an unbounded product;
- stable JSON output containing `cases`, `truncated`, `seed`, and `strategy`;
- exit code `2` with a concise stderr message for malformed input;
- no subprocess, network, filesystem mutation, or project imports.

- [ ] **Step 3: Run the helper tests red, then green**

Run:

```bash
python -m pytest tests/test_case_matrix.py -q
```

Expected before implementation: failure because the helper file does not exist. After implementation: all helper tests pass.

- [ ] **Step 4: Write the portable parameterized skill frontmatter and workflow**

Start `SKILL.md` with:

```markdown
---
name: python-parameterized-testing
description: >-
  Design, generate, run, and preserve parameterized and property-based tests
  for Python projects. Use when a user asks for table-driven cases, edge-case
  matrices, generated inputs, property-based tests, round-trip or metamorphic
  checks, invariant testing, fuzz-like exploration, or seed/replay workflows.
  Keep generated examples distinct from quantified properties and support
  pytest, unittest, or plain Python without requiring Hypothesis.
license: MIT
compatibility: Python project-agnostic; Hypothesis is optional and project
  test runners are used when available.
metadata:
  author: Nexus Envision Sdn Bhd
  version: "0.1.0"
---
```

The body must include the same structural sections as the black-box skill, plus explicit rules to state properties before generation, separate valid/invalid/unsupported domains, bound generated cases, record seeds, avoid early returns, replay and minimize failures, distinguish sampled coverage from proof, and stop before product-code changes unless requested.

- [ ] **Step 5: Add domain/property and replay references**

`domains-and-properties.md` must define fixed examples versus generated examples versus properties; valid/invalid/unsupported domains; round-trip, differential, invariant, idempotence, order, no-crash, and state-transition properties; boundary families; and oracle quality rules.

`generation-and-replay.md` must explain deterministic seeds, normalization, clocks/UUIDs/environment control, Hypothesis optional tactics, fallback tables, shrinking/minimization, explicit regressions, filtering/early-return anti-patterns, case budgets, and stateful testing only when operation sequences are the actual risk.

- [ ] **Step 6: Add the parameterized evidence template and evals**

Reuse the shared evidence fields but explicitly include property statements, valid/invalid/unsupported domains, generated witness count, discarded count, seed, replay command, shrinking status, and the statement that finite samples are not exhaustive proof.

`cases.yaml` must include positive activation, near-miss, property-vs-example distinction, seed replay, Hypothesis absence, invalid-domain handling, safety, and diagnosis-only cases.

- [ ] **Step 7: Run helper and skill checks**

Run:

```bash
python -m pytest tests/test_case_matrix.py -q
wc -l .agents/skills/python-parameterized-testing/SKILL.md
python .agents/skills/python-parameterized-testing/scripts/plan_case_matrix.py --help
```

Expected: tests pass, the core skill is below the 500-line guidance, and help exits 0.

- [ ] **Step 8: Commit the parameterized skill and helper**

```bash
git add .agents/skills/python-parameterized-testing tests/test_case_matrix.py
git commit -m "feat: add python parameterized testing skill"
```

### Task 5: Add structural and quality validation tests

**Files:**
- Create: `tests/test_skill_structure.py`
- Create: `tests/test_quality_contracts.py`

- [ ] **Step 1: Write structural tests**

`test_skill_structure.py` must discover `.agents/skills/*/SKILL.md`, parse minimal frontmatter without requiring a YAML library for the core assertions, and assert:

- `name` equals the directory name;
- `description` is non-empty and includes activation language;
- `license` is MIT;
- no client-specific frontmatter keys such as `disable-model-invocation`, `paths`, or `metadata.opencode` appear;
- every relative Markdown link resolves;
- all declared references and scripts exist;
- every `SKILL.md` is below 500 lines;
- only one canonical skill tree exists.

- [ ] **Step 2: Write quality-contract tests**

`test_quality_contracts.py` must assert each skill contains:

- `## Non-negotiable rules`;
- `## Workflow`;
- `## Failure handling`;
- `## Output contract`;
- safety terms for synthetic data and approval;
- explicit diagnosis-only/product-code language;
- a public-boundary or domain contract;
- a report path convention.

It must parse both `evals/cases.yaml` files and assert every fixture has `id`, `prompt`, `kind`, and `expected`; that each skill has at least one positive, near-miss, and safety case; and that safety cases assert approval and no silent product modification.

- [ ] **Step 3: Run validation tests and fix only concrete contract failures**

Run:

```bash
python -m pytest tests/test_skill_structure.py tests/test_quality_contracts.py -q
```

Expected: all tests pass. If a test fails because a file is missing, add the required file from Tasks 2–4; do not weaken the assertion.

- [ ] **Step 4: Commit the validation tests**

```bash
git add tests/test_skill_structure.py tests/test_quality_contracts.py
git commit -m "test: validate skill structure and quality contracts"
```

### Task 6: Add CI and skills.sh smoke validation

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `README.md` only if the verified CLI syntax differs from the documented commands

- [ ] **Step 1: Write the CI workflow**

Use a Python 3.10/3.12/3.13 matrix, install `uv`, run `uv sync`, then run:

```yaml
- run: uv run ruff check .
- run: uv run ruff format --check .
- run: uv run pytest
- run: uvx skills-ref validate .agents/skills/python-blackbox-testing
- run: uvx skills-ref validate .agents/skills/python-parameterized-testing
- run: git diff --check
```

Add a separate skills.sh discovery smoke step that lists the repository skills and fails if either skill is absent. Use a pinned or version-constrained skills CLI invocation supported by the current documentation, and do not silently install a skill into a production environment.

- [ ] **Step 2: Validate the official skill specification locally**

Run:

```bash
npx skills add . --list
uvx skills-ref validate .agents/skills/python-blackbox-testing
uvx skills-ref validate .agents/skills/python-parameterized-testing
```

Expected: both skill names are listed and both validators exit 0. If `skills-ref` is not available through the selected tool, record the exact alternative in CI rather than skipping validation silently.

- [ ] **Step 3: Run the complete local quality suite**

Run:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit CI**

```bash
git add .github/workflows/ci.yml
 git commit -m "ci: validate skills and repository tooling"
```

### Task 7: Final documentation, review, and release readiness

**Files:**
- Modify: `README.md`, `CONTRIBUTING.md`, or `CHANGELOG.md` only if verification exposes a concrete discrepancy.

- [ ] **Step 1: Review the complete diff against the approved design**

Run:

```bash
git diff main~7..HEAD --stat
git log --oneline --decorate -10
```

Check that the implementation includes the approved layout, both skill contracts, research report, community files, tests, helper, CI, and no duplicated skill tree.

- [ ] **Step 2: Run security and content checks**

Run:

```bash
rg -n 'BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY|AKIA[0-9A-Z]{16}' . --glob '!uv.lock'
rg -n 'shell=True|requests\.|subprocess\.' .agents/skills/python-parameterized-testing/scripts tests
```

Expected: no credentials, no `shell=True`, no network import in the helper, and no unapproved subprocess usage in the helper. Any target-project commands shown in Markdown must be examples or safety-gated instructions, not repository automation.

- [ ] **Step 3: Verify the install and skill smoke tests from a clean checkout**

Run:

```bash
git status --short --branch
npx skills add . --list
```

Expected: a clean working tree after committed changes and both skills discoverable by skills.sh.

- [ ] **Step 4: Update the changelog only for verified v0.1.0 content**

Record the two skill names, install command, framework-agnostic behavior, and the verification commands that passed. Do not claim adoption, quality ranking, or semantic-eval success.

- [ ] **Step 5: Commit final documentation and report the evidence**

```bash
git add README.md CONTRIBUTING.md CHANGELOG.md
 git commit -m "docs: finalize initial skill release"
```

Report the final commit, exact test commands, pass/fail counts, and any checks that could not be run.
