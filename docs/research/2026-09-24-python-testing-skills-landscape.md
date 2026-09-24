# Python Testing Skills Landscape

Date: 2026-09-24
Scope: skills.sh packaging, adoption signals, and primary-source Python testing guidance
Evidence basis: skills.sh public pages and official repositories; Agent Skills, Python, pytest, Hypothesis, and Pact documentation

> Install counts are deduplicated CLI telemetry, not unique users or successful executions. Repository-level GitHub metrics are secondary signals and do not isolate adoption of an individual skill.

## 1. Executive summary

The evidence supports six factors for an excellent Python testing skill:

1. **A precise activation boundary.** The Agent Skills specification says `description` states both what a skill does and when to use it; skill-author guidance recommends coherent units, explicit procedures, and concrete defaults rather than menus ([specification](https://agentskills.io/specification), [best practices](https://agentskills.io/skill-creation/best-practices)).
2. **Behavior at a public boundary, checked by an independent oracle.** The practical test-pyramid guidance favors observable behavior and public interfaces over private implementation, while mattpocock's `tdd` skill requires expected values to come from a literal, worked example, or specification rather than recomputing the implementation ([Fowler](https://martinfowler.com/articles/practical-test-pyramid.html#WhatToTest), [`tdd` source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md)).
3. **A short, executable feedback loop with hard evidence gates.** `diagnosing-bugs` requires one runnable red-capable command; `systematic-debugging` blocks fixes until root-cause work is complete; and `verification-before-completion` requires fresh command output before a passing claim ([diagnosing source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md), [systematic source](https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/systematic-debugging/SKILL.md), [verification source](https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/verification-before-completion/SKILL.md)).
4. **Examples plus properties, with isolation and cleanup.** `unittest` defines isolated test cases and setup/teardown; pytest fixtures provide fresh state and finalization; Hypothesis describes property testing as an addition to, not a replacement for, example-driven unit tests ([unittest](https://docs.python.org/3/library/unittest.html), [pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html), [Hypothesis introduction](https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html)).
5. **Inspectable evidence with bounded replay.** Preserve commands, seeds, minimized inputs, test IDs, and exact pass/fail/skip counts. Hypothesis local databases and reproduction blobs support local or CI replay, but current documentation warns that database entries can be invalidated by upgrades or source changes and blobs are not stable across versions; use explicit fixed examples for durable regression evidence ([Hypothesis replay](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html), [Hypothesis settings](https://hypothesis.readthedocs.io/en/latest/reference/api.html#settings), [skills.sh API](https://www.skills.sh/docs/api)).
6. **Low-friction distribution with explicit safety.** A skills.sh detail page exposes a one-command install, while the CLI's shared format lowers porting cost. That format does not remove the need to review scripts, treat retrieved content as untrusted, redact secrets, and separate read-only tests from live or destructive operations ([skills.sh CLI](https://www.skills.sh/docs/cli), [CLI source](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/README.md#install-a-skill), [Snyk threat research](https://research.snyk.io/blog/agent-skills-threat-landscape/)).

**Finding versus inference:** the cited documentation and source files establish the behavior below. Statements beginning “Design inference” translate that evidence into choices for the two future skills; they are not claims that the surveyed skills determined their install counts or that popularity establishes quality.

## 2. Packaging and compatibility

### Install surface

skills.sh documents the `npx skills add` command and exposes copyable commands on each detail page. Concrete examples are:

```bash
npx skills add https://github.com/mattpocock/skills --skill tdd
npx skills add https://github.com/obra/superpowers --skill systematic-debugging
```

The CLI accepts a repository plus `--skill`, can target one or more agents, and defaults to project installation ([CLI reference](https://www.skills.sh/docs/cli), [CLI source](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/README.md#options)). A maintainer should therefore publish each skill in a discoverable `skills/<name>/SKILL.md` layout and make the detail page's install command the primary setup path, rather than documenting a manual file copy.

### `.agents/skills` decision

**Decision:** keep the checked-in canonical copies under `.agents/skills/<skill-name>/SKILL.md`.

**Evidence:** the skills CLI lists `.agents/skills/` as the project path for Amp, Replit, Universal, Antigravity, Codex, Cursor, Deep Agents, Droid, Firebender, Gemini CLI, GitHub Copilot, Kilo Code, OpenCode, PromptScript, and others. It also supports canonical-copy symlinks to agent-specific directories ([supported agents and installation scope](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/README.md#installation-scope)).

**Compatibility caveat:** the Agent Skills specification defines the `SKILL.md` format, not a universal discovery algorithm. Claude Code and several other clients use product-specific project paths; Kiro custom agents need resources configured. The CLI's compatibility table also marks some frontmatter capabilities as experimental or unsupported by particular clients ([specification](https://agentskills.io/specification), [client compatibility](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/README.md#compatibility)). Therefore:

- use only required `name` and `description` frontmatter for the broadest baseline;
- put deeper material in relative `references/`, `scripts/`, and `assets/` paths as the specification recommends;
- omit experimental `allowed-tools` unless the skill also states its compatibility limitation;
- document an explicit `npx skills add https://github.com/obra/superpowers --skill systematic-debugging --agent claude-code` path for clients that do not discover `.agents/skills` directly;
- test the exact installed tree in at least the repository's target clients, rather than assuming directory placement equals discovery.

## 3. Adoption snapshot

The figures below are the research snapshot dated 2026-09-24, accessed from the live skills.sh detail pages on that date. The live pages and ranks are mutable, so these links identify the source pages but do not preserve the historical values. No archived skills.sh response or immutable snapshot URL for these figures was available in the source set; the values below are therefore a dated observation, not a reproducible current response.

| Rank | Skill | Installs | Detail page |
|---:|---|---:|---|
| 5 | `mattpocock/skills/tdd` | 955,803 | [skills.sh detail](https://www.skills.sh/mattpocock/skills/tdd) |
| 44 | `mattpocock/skills/diagnosing-bugs` | 654,838 | [skills.sh detail](https://www.skills.sh/mattpocock/skills/diagnosing-bugs) |
| 53 | `mattpocock/skills/code-review` | 606,655 | [skills.sh detail](https://www.skills.sh/mattpocock/skills/code-review) |
| 235 | `obra/superpowers/systematic-debugging` | 269,465 | [skills.sh detail](https://www.skills.sh/obra/superpowers/systematic-debugging) |
| 259 | `obra/superpowers/verification-before-completion` | 219,671 | [skills.sh detail](https://www.skills.sh/obra/superpowers/verification-before-completion) |

These figures show distribution reach, not successful outcomes. The skills.sh API describes `installs` as a **total deduplicated install count**; its CLI documentation says ranking is based on anonymous install telemetry, which users can disable ([API](https://www.skills.sh/docs/api), [overview](https://www.skills.sh/docs), [CLI telemetry](https://www.skills.sh/docs/cli)). The count does not reveal unique people, retained installations, invocations, useful runs, satisfaction, or code quality. Rank can also change after this snapshot. GitHub stars, forks, and commits describe the containing repository rather than one skill, so they should not be used to infer an individual skill's adoption.

### Secondary repository signals

These are the research snapshot's secondary GitHub values, not skill-specific adoption data. The interval is 2026-08-24 through 2026-09-24; repository pages are mutable, and no archived metrics response is included.

| Repository | Stars | Forks | Contributors | Commits in interval | Default-branch history | Releases |
|---|---:|---:|---:|---:|---:|---:|
| [vercel-labs/skills](https://github.com/vercel-labs/skills/tree/7407f3893ad4dceab546ac002c3ef806e4000c73) | 32,357 | 2,757 | 147 | 42 | 520 | 47 |
| [mattpocock/skills](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7) | 268,552 | 22,641 | 8 | 18 | 472 | 7 |
| [anthropics/skills](https://github.com/anthropics/skills) | 177,841 | 21,067 | 16 | 3 | 55 | 0 |
| [obra/superpowers](https://github.com/obra/superpowers/tree/5bf4e78011075bcfc0dc295f0724994cd123ee71) | 290,756 | 26,018 | 44 | 1 | 682 | 13 |
| [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli/tree/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5) | 13,519 | 748 | 13 | 9 | 111 | 24 |

These signals are useful for repository maintenance and ecosystem context, but they do not isolate the two skills in this report or substitute for the skills.sh telemetry above.

## 4. What popular skills do differently

| Factor | Evidence in surveyed sources | Design inference from the evidence |
|---|---|---|
| Evidence vs inference | Agent Skills guidance says to extract skills from real tasks, project artifacts, corrections, and execution traces, then revise from actual runs ([best practices](https://agentskills.io/skill-creation/best-practices)). | Build evaluation cases from real Python repositories and retain failures and false triggers as skill feedback. Do not infer success from installs. |
| Sharp triggers | The specification asks descriptions to include what and when; `tdd`, `diagnosing-bugs`, `systematic-debugging`, and `verification-before-completion` use explicit phrases such as “test-first,” “broken/failing/slow,” “before proposing fixes,” and “before claiming” ([sources](https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering)). | Give each testing skill a non-overlapping trigger vocabulary: examples/parameterization versus generated properties, plus a shared boundary to verification. |
| Executable loops | mattpocock `tdd` specifies red → green, one vertical slice at a time. `diagnosing-bugs` requires a named command already run against the actual symptom. Playwright CLI supplies concrete commands and machine-readable output ([`tdd`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md), [`diagnosing-bugs`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md), [playwright-cli](https://github.com/microsoft/playwright-cli/blob/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5/skills/playwright-cli/SKILL.md)). | Make the smallest relevant test command the first artifact, then expand to focused and full-suite commands. |
| Hard gates | systematic-debugging says no fix without root-cause investigation; verification-before-completion requires identify → run → read → verify → claim; `tdd` requires a failing test before green ([sources](https://github.com/obra/superpowers/tree/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills)). | Gate completion on observed red/green evidence and report unmet gates as unmet, not as a successful test run. |
| Inspectable artifacts | `diagnosing-bugs` shows redacted commands, outputs, captured artifacts, and hypotheses. `code-review` pins a diff and reports Standards and Spec axes separately. Playwright's official skill documents snapshots, generated locators, screenshots, raw/JSON output, and tracing commands ([diagnosing source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md), [code-review source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/code-review/SKILL.md), [Playwright source](https://github.com/microsoft/playwright-cli/blob/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5/skills/playwright-cli/SKILL.md)). | Preserve exact commands, IDs, seeds, minimized cases, oracle, and counts. Keep Standards/Spec-style axes separate: expected result versus implementation conformance. |
| Progressive disclosure | The specification recommends metadata, a focused `SKILL.md` under 500 lines, and on-demand references/scripts/assets. mattpocock `tdd` links `tests.md` and `mocking.md`; playwright-cli routes specialized tasks to reference files ([specification](https://agentskills.io/specification#progressive-disclosure), [`tdd`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md), [playwright-cli](https://github.com/microsoft/playwright-cli/blob/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5/skills/playwright-cli/SKILL.md)). | Keep the core decision loop inline; place large framework recipes, oracle patterns, and strategy catalogs behind explicit “read when” triggers. |
| Fast feedback | `diagnosing-bugs` defines a fast, deterministic, red-capable loop; the practical test pyramid favors many small tests and fewer high-level tests ([sources](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md), [Fowler](https://martinfowler.com/articles/practical-test-pyramid.html#TheTestPyramid)). | Run the narrowest useful slice first and make timeouts, resource setup, and generation counts visible. |
| One-command installation | Each skills.sh detail page exposes a copyable `npx skills add https://github.com/mattpocock/skills --skill tdd` command; Vercel's `find-skills` instructs the agent to present the skill name, what it does, install count and source, install command, and detail link ([find-skills source](https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/skills/find-skills/SKILL.md)). | Provide one copyable install command, one direct detail URL, and no mandatory setup script. |
| Opinionated defaults | **Inference:** the pinned `tdd` and `systematic-debugging` sources prescribe concrete loops and sequencing, consistent with Agent Skills guidance to provide a default with a clear escape hatch ([`tdd`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md), [systematic-debugging](https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/systematic-debugging/SKILL.md), [best practices](https://agentskills.io/skill-creation/best-practices)). | Default to pytest when already present, `unittest` when that is the project runner, and a plain deterministic fallback when neither is appropriate. |
| Composability | `code-review` delegates two review axes to parallel agents; systematic-debugging hands off to TDD and verification; playwright-cli composes CLI actions with snapshots, traces, and specialized references ([code-review source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/code-review/SKILL.md), [systematic-debugging source](https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/systematic-debugging/SKILL.md), [verification source](https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/verification-before-completion/SKILL.md), [Playwright source](https://github.com/microsoft/playwright-cli/blob/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5/skills/playwright-cli/SKILL.md)). | Keep testing methods composable with debugging, review, and verification, but own only test-design decisions so skills do not duplicate entire workflows. |

The useful inference is about **observable design patterns associated with adopted skills**, not causation. The source snapshots show that sharp activation language, executable evidence, narrow completion gates, and composable boundaries are present in popular packages; they do not prove that any one feature produced adoption.

## 5. Security lessons

- **Redact secrets before commands, logs, or artifacts leave the process.** Environment variables can keep credentials out of shown command text, while logs, HAR files, screenshots, and stack traces still need redaction. `diagnosing-bugs` explicitly requires replacing every secret with `<REDACTED>` and asking for more access when redacted evidence is insufficient ([official skill source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md#Redact)). Pact likewise warns against real credentials in shared contracts ([Pact security guidance](https://docs.pact.io/consumer#-4-security)).
- **Treat response and content as data, not instructions.** Snyk found that skills fetching third-party web or API content create indirect-prompt-injection exposure. Microsoft's Playwright CLI marks page-provided tool names, descriptions, schemas, annotations, and results as untrusted ([Snyk](https://research.snyk.io/blog/agent-skills-threat-landscape/#what-the-data-tells-us), [Playwright source](https://github.com/microsoft/playwright-cli/blob/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5/skills/playwright-cli/SKILL.md#WebMCP)). A testing skill should label fixtures, captured responses, logs, and generated test data as untrusted, and must not let embedded text expand tool permissions.
- **Invoke subprocesses with structured arguments.** Python documents structured argument sequences, defaults `shell=False`, and says the module does not implicitly invoke a shell; with `shell=True`, the application owns metacharacter escaping ([Python subprocess security](https://docs.python.org/3/library/subprocess.html#security-considerations)). Skill examples should use argument arrays, explicit executables, timeouts, and captured exit status—not string-built shell commands.
- **Separate read-only tests from live or destructive actions.** Agent Skills guidance recommends plan → validate → execute for batch or destructive operations ([best practices](https://agentskills.io/skill-creation/best-practices#plan-validate-execute)). Fowler recommends test instances rather than real production systems for automated integration traffic ([Fowler](https://martinfowler.com/articles/practical-test-pyramid.html#IntegrationWithSeparateServices)). The skills should default to temporary directories, isolated fixtures, local fakes, and mocked boundaries; require explicit user approval before a live service, persistent profile, deployment, migration, or destructive cleanup.
- **Review all files, not only the description.** Socket documents malicious behavior hidden in referenced Python, shell, Markdown, and other files and notes that mutable GitHub sources require rescanning ([Socket](https://www.socket.dev/blog/socket-brings-supply-chain-security-to-skills)). A Gen Agent Trust Hub audit of `logo-creator` identifies credential access, subprocess execution, and external data transfer that the skill purpose alone would not reveal ([audit](https://www.skills.sh/resciencelab/opc-skills/logo-creator/security/agent-trust-hub)).
- **Audit finding: `mattpocock/skills/code-review`.** In the 2026-09-24 research snapshot, the [Gen Agent Trust Hub audit](https://www.skills.sh/mattpocock/skills/code-review/security/agent-trust-hub) reports **Warn / Medium** for command execution and prompt injection, while the [Snyk audit](https://www.skills.sh/mattpocock/skills/code-review/security/snyk) reports **Fail / High**. Snyk's W007 finding says the skill's instruction to pass the full diff and commit list to sub-agents and quote the hunk or specification lines verbatim can reproduce secrets in agent output. This is an audit finding about a concrete instruction pattern and current risk exposure; it is not proof that the skill is inherently unsafe. Users should review the [pinned skill source](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/code-review/SKILL.md), treat repository content as untrusted, and redact or bound quoted material before adoption.
- **Popularity is not a safety signal.** Snyk explicitly says download counts can be inflated and recommends source review and scanning. skills.sh also asks users to review skills and does not promise that every listed skill is secure ([Snyk](https://research.snyk.io/blog/agent-skills-threat-landscape/#recommendations), [skills.sh](https://www.skills.sh/docs#how-are-you-securing-skills)). An audit verdict is another review input, not proof of harmless runtime behavior.

## 6. Python testing guidance

- **Public boundaries.** Test observable behavior through a public function, class, CLI, or client boundary. Avoid private methods, internal call order, and side-channel assertions. The practical pyramid says implementation-coupled tests break under refactoring and recommends the public interface; Pact scopes consumer contracts to the API client rather than the whole UI or provider ([Fowler](https://martinfowler.com/articles/practical-test-pyramid.html#WhatToTest), [Pact](https://docs.pact.io/consumer#use-pact-for-isolated-unit-tests)).
- **Independent oracles.** Derive expected outcomes from a specification, known-good literal, worked example, approved contract, or a simpler trusted model—not from the same algorithm under test. Keep production-like state and side effects out of the oracle.
- **Isolation and cleanup.** `unittest` says each `TestCase` should be self-contained and run in isolation or arbitrary combination; it creates a fresh fixture per test method and runs `tearDown()` after a successful setup ([unittest organization](https://docs.python.org/3/library/unittest.html#organizing-test-code)). pytest recommends function-scoped fresh state and `yield` fixture teardown; shared scopes are appropriate for expensive resources only when mutation is controlled ([fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html#fixtures-are-reusable), [teardown](https://docs.pytest.org/en/stable/how-to/fixtures.html#teardown-cleanup-aka-fixture-finalization)).
- **Negative and edge cases.** Alongside the successful path, exercise malformed input, empty/boundary values, denied access, wrong exceptions, and relevant external failures. `unittest` provides `assertRaises`, warning/log assertions, and `subTest`; pytest's parameter IDs make each input visible on failure ([unittest assertions](https://docs.python.org/3/library/unittest.html#assert-methods), [parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html)).
- **Examples versus properties.** Use examples to pin known scenarios and communicate specification decisions. Use properties for invariants, round trips, equivalence, and generated edge domains. Hypothesis calls property-based testing an addition to unit testing and suggests it for round trips, reference-model equivalence, crashes on valid inputs, and replacing large parameter ranges ([Hypothesis introduction](https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html#when-to-use-hypothesis-and-property-based-testing)).
- **Replay and shrinking.** Record seed, command, environment assumptions, and minimized input. **Current documentation caveat (accessed 2026-09-24):** Hypothesis's local `ExampleDatabase` is for quick local replay, and its entries can be invalidated by an upgrade or source change; `@reproduce_failure` blobs are version-sensitive and should remain temporary. Use explicit `@example` inputs for durable regression evidence. Hypothesis can still print a reproduction blob when `settings.print_blob=True` and can shrink failures toward a minimal test case ([replay tutorial](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html), [reproduction API](https://hypothesis.readthedocs.io/en/latest/reference/api.html#reproduce_failure), [settings](https://hypothesis.readthedocs.io/en/latest/reference/api.html#settings)).
- **Hypothesis remains optional.** It is an installable third-party library, while `unittest` ships with Python. The property skill should detect it, use it when present, and avoid adding a mandatory dependency to a generic project. Without Hypothesis, fall back to explicit pytest parameters, `unittest.subTest`, or a deterministic seeded corpus with the seed printed. Label that fallback honestly: it lacks Hypothesis's adaptive generation and shrinking.
- **Contracts at boundaries.** Pact recommends isolated consumer API-client tests, least-strict matching that still catches consumer breakage, deterministic contract data, and fake data rather than secrets. It separates contract checks from provider functional testing ([Pact consumer guide](https://docs.pact.io/consumer)).
- **A practical portfolio, not dogma.** Fowler's practical pyramid favors many fast low-level tests, some integration/contract tests, and few high-level end-to-end tests while warning that layer names can mislead ([Fowler](https://martinfowler.com/articles/practical-test-pyramid.html#TheTestPyramid)). Let the skill spend test budget by risk and feedback speed, not by a fixed ratio.
- **Honest status.** Report passed, failed, errored, xfailed/expected-failure, and skipped/not-run separately, with reasons. `unittest` explicitly reports skips and does not run setup/teardown for skipped tests; pytest reports an empty parameter set as skipped ([unittest skipping](https://docs.python.org/3/library/unittest.html#skipping-tests-and-expected-failures), [pytest parameterization](https://docs.pytest.org/en/stable/how-to/parametrize.html#basic-pytest-generate-tests-example)). A skipped test must never be folded into a passing count without its status and reason.

## 7. Design implications

For clarity, **example skill** means the future example/parameterization-oriented Python testing skill, and **property skill** means the future property-based/parameterized Python testing skill. The first column separates sourced findings from design inference; all second-column choices are design inference.

| Factor | Evidence-backed finding | Example skill: concrete choice | Property skill: concrete choice |
|---|---|---|---|
| Sharp scope and triggers | Descriptions must say what and when; procedures should be coherent. | Trigger on named scenarios, tables/cases, edge matrices, `pytest.mark.parametrize`, and `unittest.subTest`; route generated properties elsewhere. | Trigger on invariants, round trips, generators, Hypothesis, shrinking, and generated regressions; route fixed examples to the example skill. |
| Public boundary and oracle | Public behavior and independent oracles reduce implementation coupling. | Require a public call and a spec/literal/worked-example oracle before writing the assertion. | Require a public call plus an invariant or trusted simpler model; reject a “property” that only repeats the implementation. |
| Executable loop and hard gate | Popular debugging/review skills expose commands and block unsupported progress. | Cycle: select one scenario → run to observe expected fail/pass → add only the next case → run focused command. No green claim without fresh output. | Cycle: state property → run and preserve seed plus any versioned local replay blob → minimize → add an explicit fixed regression example → rerun focused and broader suites. No property claim without observed coverage. |
| Inspectable artifacts | Commands, hypotheses, diffs, snapshots, and local replay records are inspectable evidence. | Record node/test ID, parameter row, oracle, command, exit status, and pass/fail/skip counts. | Record property, strategy/domain, seed, example count, shrink result, Hypothesis version, and an explicit fixed regression example in addition to the test ID. |
| Progressive disclosure | Core instructions should load first; references and scripts load on demand. | Inline the decision loop; move pytest/unittest recipes, negative-case matrices, and Pact guidance to focused references. | Inline property selection and safety rules; move strategy catalogs, shrinking/replay details, and framework adapters to focused references. |
| Fast feedback and portfolio | Tight loops and a high-volume low-level tier are favored. | Start with one case; parameterize close variants; reserve HTTP/UI work for narrow boundaries. | Start with bounded examples and a small maximum-case budget; expand only after the property is valid and fast. |
| Isolation and cleanup | Fresh fixtures and reliable teardown protect repeatability. | Default to temporary directories, isolated state, fake external boundaries, and deterministic clocks/seeds. | Require fresh state per generated case where mutation occurs; prevent one generated case from contaminating the next. |
| Safe subprocesses and live effects | Structured argument execution and explicit destructive gates reduce injection and accidental impact. | Use runner commands as argument arrays with timeouts; require approval for live services, persistent profiles, migrations, and destructive cleanup. | Apply the same execution boundary; add approval for stateful fuzz harnesses, remote corpora, and any live target. |
| Opinionated defaults | Guidance favors one default with an escape hatch. | Default to the repository's existing runner; prefer pytest parameters, fall back to `unittest.subTest`, and offer a plain deterministic loop only as the last resort. | Default to Hypothesis when installed; otherwise use a seeded deterministic corpus and state the reduced assurances. |
| Composability | Adopted skills hand work to focused adjacent skills. | Own case/oracle design; hand root-cause work to debugging, review separation to code review, and completion claims to verification. | Own property generation/minimization; hand failure diagnosis to debugging and final status claims to verification. |
| Packaging and discovery | A shared format and one-command CLI are portable, but client discovery varies. | Publish under `.agents/skills/`, provide a skills.sh copyable install command, and document alternate-client installation. | Mirror the same compatibility baseline; do not duplicate shared setup/security guidance. |
| Honest reporting | Skips and expected failures are distinct from passes. | Report each parameter row and collection/skip status, including an empty matrix. | Report example counts, invalid/filtered cases, skipped property modules, and whether shrinking/replay ran. |

The two skills should share a small security/reporting contract but not collapse into one large document. That preserves progressive disclosure and precise triggers while allowing an agent to compose only the testing method the task needs.

## 8. References

All URLs were accessed 2026-09-24.

### Packaging and skill guidance

1. Agent Skills specification — https://agentskills.io/specification
2. Agent Skills best practices — https://agentskills.io/skill-creation/best-practices
3. skills.sh CLI reference — https://www.skills.sh/docs/cli
4. skills.sh documentation — https://www.skills.sh/docs
5. skills.sh API reference — https://www.skills.sh/docs/api
6. skills CLI source and compatibility matrix — https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/README.md

### Adoption pages and official skill sources

7. `mattpocock/skills/tdd` detail — https://www.skills.sh/mattpocock/skills/tdd
8. `mattpocock/skills/diagnosing-bugs` detail — https://www.skills.sh/mattpocock/skills/diagnosing-bugs
9. `mattpocock/skills/code-review` detail — https://www.skills.sh/mattpocock/skills/code-review
10. `obra/superpowers/systematic-debugging` detail — https://www.skills.sh/obra/superpowers/systematic-debugging
11. `obra/superpowers/verification-before-completion` detail — https://www.skills.sh/obra/superpowers/verification-before-completion
12. mattpocock `tdd` source — https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md
13. mattpocock `diagnosing-bugs` source — https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md
14. mattpocock `code-review` source — https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/code-review/SKILL.md
15. obra `systematic-debugging` source — https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/systematic-debugging/SKILL.md
16. obra `verification-before-completion` source — https://github.com/obra/superpowers/blob/5bf4e78011075bcfc0dc295f0724994cd123ee71/skills/verification-before-completion/SKILL.md
17. Vercel `find-skills` source — https://github.com/vercel-labs/skills/blob/7407f3893ad4dceab546ac002c3ef806e4000c73/skills/find-skills/SKILL.md
18. Microsoft Playwright CLI skill source — https://github.com/microsoft/playwright-cli/blob/74354ecc7a43da16d91a9bc54fa8db8283a3fcf5/skills/playwright-cli/SKILL.md

### Python testing and security

19. Python `unittest` — https://docs.python.org/3/library/unittest.html
20. Python `subprocess` — https://docs.python.org/3/library/subprocess.html
21. pytest fixtures — https://docs.pytest.org/en/stable/how-to/fixtures.html
22. pytest parametrization — https://docs.pytest.org/en/stable/how-to/parametrize.html
23. Hypothesis introduction — https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html
24. Hypothesis API — https://hypothesis.readthedocs.io/en/latest/reference/api.html
25. Hypothesis replaying failed tests — https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html
26. Hypothesis reproduction and settings API — https://hypothesis.readthedocs.io/en/latest/reference/api.html#reproduce_failure
27. Pact consumer testing — https://docs.pact.io/consumer
28. The Practical Test Pyramid — https://martinfowler.com/articles/practical-test-pyramid.html
29. Snyk agent-skills threat landscape — https://research.snyk.io/blog/agent-skills-threat-landscape/
30. Socket skills.sh scanning — https://www.socket.dev/blog/socket-brings-supply-chain-security-to-skills
31. Gen Agent Trust Hub `logo-creator` audit — https://www.skills.sh/resciencelab/opc-skills/logo-creator/security/agent-trust-hub
32. Gen Agent Trust Hub `code-review` audit — https://www.skills.sh/mattpocock/skills/code-review/security/agent-trust-hub
33. Snyk `code-review` audit — https://www.skills.sh/mattpocock/skills/code-review/security/snyk
