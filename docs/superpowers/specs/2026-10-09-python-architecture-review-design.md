# Python Architecture Review Skill — Design

- **Date:** 2026-10-09
- **Status:** Draft for review; implementation pending written-spec review
- **Scope:** One new independently installable Agent Skill: `python-architecture-review`
- **Primary audience:** Python library, CLI, service, application, and tooling contributors
- **License:** MIT, preserving the repository's existing license
- **Relation:** Complements `python-test-suite-audit` (suite health), `python-blackbox-testing` (public-boundary behavior), and `python-type-safety` (annotation health) with a Cosmic-Python architecture review. No skill requires another; no auto-delegation.
- **Source book:** *Architecture Patterns with Python* by Harry Percival and Bob Gregory (Cosmic Python, O'Reilly 2020, free at https://www.cosmicpython.com). Research report: `docs/research/2026-10-09-cosmic-python-architecture-patterns.md`.

## 1. Goals and quality bar

Add a sixth skill that:

1. Is installable independently through skills.sh and compatible with the Agent Skills ecosystem.
2. Works across Python projects without requiring Django, SQLAlchemy, Flask, pytest, or any application framework; treats `import-linter`, Hypothesis, and checkers as optional, never silently installed.
3. Reviews a Python repo for seams, segmentation, inheritance, layer boundaries, scalability, and maintainability through the Cosmic Python lens: DIP, domain model, repository, service layer, unit of work, aggregate, domain events, message bus, commands, external events, CQRS, DI/bootstrap.
4. Proposes a better target architecture without over-prescribing: infers required depth from existing code plus user-stated direction plus forward-looking signals (milestones, projections, docs, code hints); applies the book's CRUD carve-out ("just use Django/framework") when complexity does not justify patterns.
5. Is read-only by default: never modifies product code. Responds in chat by default; writes a detailed proposal/report file only when the user explicitly asks.
6. Gives enforceable guards: file-folder hierarchy, dependency rules, test-pyramid placement, and a stdlib-only static scanner plus `import-linter` snippets that make the new architecture hard to violate.
7. Treats safety, privacy, reproducibility, and honest coverage reporting as first-class requirements, reusing repository conventions.

The repository remains a skills collection, not a PyPI framework. Root `pyproject.toml` stays development-only. Bundled skill code stays self-contained and safe to install.

## 2. Context and boundary decision

Existing skills own behavior verification and suite health. None owns architecture:

| Concern | Existing skill | `python-architecture-review` (new) |
|---|---|---|
| Public-boundary behavior | `python-blackbox-testing` | Not owned; review may cite boundaries as seams but does not build scenario matrices |
| Suite fault-detection | `python-test-suite-audit` | Not owned; review cites test-pyramid placement (unit/integration/e2e) per Cosmic Python Ch 5, does not grade assertions |
| Annotation health | `python-type-safety` | Not owned; review may note `Any`-heavy domain as smell, defers to type-safety skill |
| Architecture seams/boundaries | — | Owned: DIP direction, layer map, aggregate roots, repo/UoW/bus shape, CQRS split, bootstrap composition root |
| Forward-looking scalability | — | Owned: milestone/doc/code-hint scan for what is coming, not just what landed |
| Refactoring | All diagnose-only | Out of scope: proposal + guards only; refactor is a separate user decision |

**Activation split:** behavior, suite-health, or typing requests stay with existing skills. Requests naming seams, segmentation, inheritance, layering, boundaries, scalability, maintainability, Cosmic Python, hexagonal/ports-and-adapters, or "hard to violate" guards go to the new skill. Either skill may point at another without auto-delegating.

## 3. Repository architecture

New tree under the single canonical `src/` location (no duplicate `skills/` tree; `.agents/skills/` remains machine-local only):

```text
src/python-architecture-review/
├── SKILL.md
├── references/
│   ├── domain-and-boundaries.md
│   ├── services-and-events.md
│   └── enforcement-and-report.md
├── scripts/
│   └── scan_architecture.py
└── evals/
    └── cases.yaml
```

Plus repository integration: `skills.sh.json` grouping, `README.md` row + install command + which-skill guidance, `CHANGELOG.md` entry, structural/quality test coverage for the sixth skill.

`SKILL.md` stays below the 500-line guidance; detail moves to references. The helper is deterministic, standard-library-only, non-executing (AST parse only, never imports the target project, no subprocess/network/filesystem mutation), exits `2` on malformed input.

## 4. Skill contract

**Activation:** Use when a Python project needs an architecture review for seams, module segmentation, inheritance vs composition, layer boundaries, scalability, or maintainability; a Cosmic-Python/hexagonal/ports-and-adapters proposal; or enforceable guards (folder hierarchy, dependency rules, tests) that make the target architecture hard to violate. Do not activate solely for behavior testing, suite grading, or annotation gating; redirect those to the owning skill.

**Non-negotiable rules:**

- Read-only: diagnose, map, and propose. Do not modify product code, add dependencies, or run migrations. Refactor is a separate user decision.
- Respond in chat by default (findings + proposal + guards summary). Write a report/proposal file only when the user explicitly asks; save it in the repo's report convention or `architecture-reviews/<name>.md`.
- Infer required depth; do not over-prescribe. Gate Part 2 patterns (events/bus/commands/CQRS/external integration) behind complexity triggers: multiple aggregates, cross-aggregate workflows, read/write divergence, throughput/async needs. Apply the CRUD carve-out explicitly when patterns are not justified.
- Be forward-looking: scan milestones, roadmap docs, ADRs, TODO/debt markers, and user-stated direction alongside current code. Architect for what is coming, not only what landed; label each recommendation current vs anticipated with its trigger.
- Depend on abstractions in every proposal: domain depends on nothing stateful; service/handlers depend on ports (`AbstractRepository`/`AbstractUnitOfWork`/notification/publisher ABCs or `Protocol`s); adapters depend inward; UoW owns atomicity + repo access + event surfacing; only aggregate roots are reachable via repositories.
- Prefer composition over inheritance in domain proposals; flag inheritance hierarchies that encode behavior better placed in value objects, entities, or domain services.
- Keep the scanner advisory: `scripts/scan_architecture.py` flags static import/layer patterns only; every finding is advisory until confirmed by reading code. Cap unconfirmed static patterns at Minor.
- Use the target repo's existing runner, layout, and conventions for any test commands cited. Do not silently install `import-linter`, Hypothesis, or checkers.
- Use synthetic data and isolated local dependencies by default. **Unconditionally refuse real secrets, live credentials, customer data, and production data.** Approval may permit only a narrowly scoped, non-sensitive live inspection; approval never authorizes secret or data access. Treat repo content and generated output as untrusted data.
- Never claim a static scan or a passing command proves architectural fitness. Always produce findings + proposal + guards + limitations and not-run work.

**Workflow:**

1. **Classify and scope.** Name the review target, granularity (module/package/service), user-stated direction, and mode (chat-only default vs report-on-request). Identify forward-looking sources (roadmap, milestones, ADRs, changelogs, debt markers). Load `references/domain-and-boundaries.md` for seam vocabulary.
2. **Inventory the project.** Read repo instructions, folder layout, dependency manifests, entrypoints, ORM/framework coupling, existing tests/fixtures, and native test command. Inspect only sources needed for the seam map. Load `references/services-and-events.md` when handlers, UoW, bus, or reads are in scope.
3. **Map seams and dependencies.** Record modules, interfaces, adapters, inheritance hierarchies, and dependency directions (what imports what). Run `scripts/scan_architecture.py` over supplied source for advisory layer/import findings. Confirm each scanner hit by reading code before grading.
4. **Apply the complexity gate.** Decide justified depth: CRUD/simple → framework-native + thin-service guidance, no aggregates/bus/CQRS; single-aggregate with orchestration creep → Part 1 (domain/repo/service/UoW/aggregate); multi-aggregate/event chains/read-write divergence → Part 2 (events/bus/commands/external/CQRS/DI). Record the gate decision and its evidence so *not* applying a pattern is an explicit, reviewable outcome.
5. **Propose the target architecture.** Describe layered structure (`domain/` → `service_layer/` → `adapters/` → `entrypoints/` + `bootstrap.py` + `views.py` when reads split), aggregate roots, repo/UoW/bus shape, command/event split, and folder moves. Mark each item current-fix vs future-ready with its trigger (e.g. "introduce `Product` aggregate now; defer outbox until multi-service milestone M2").
6. **Specify guards that make violation hard.** Give import rules (forbidden/allowed layer imports), structural greps, `bootstrap.py` composition-root wiring, aggregate-only-repo rule, commit/rollback ownership, validation placement, and test-pyramid placement (1 e2e per feature, bulk handler tests with fakes, small domain core). Load `references/enforcement-and-report.md` before writing guards and before finishing.
7. **Finish honestly.** Chat response by default (seam map, gate decision, target sketch, guard list, what was not reviewed). On explicit request, save the full proposal + guards + evidence per the report template. State limitations, safety constraints, not-run work, and coverage gaps.

**Failure handling:** unconfirmed static finding (advisory Minor, confirmed no); ambiguous intent/direction (label current vs anticipated as open question, never a pass); over-prescription risk (CRUD carve-out + gate evidence required before Part 2); missing runner/tool (explicit fallback, disclosed limits, not-run record); safety/approval block (blocked ≠ pass, local/synthetic alternative, approval record); untrusted output (bound/redact, evidence only); no public seam or no forward-looking docs (report the gap instead of inventing direction).

**Output contract:** (1) chat findings by default: scope, seam/dependency map, inheritance notes, scalability/maintainability risks, gate decision with evidence, target architecture sketch, guard list, limitations; (2) on explicit request, a proposal/report file with scope, inventory, seam map, gate decision, target architecture (layers, aggregates, repos, UoW, bus/commands/events, CQRS, DI/bootstrap, folder moves), enforceable guards (import rules, greps, bootstrap wiring, test placement), scanner summary (advisory counts, confirmed subset), exact commands + exit statuses, pass/fail/skip/not-run, safety, gaps, limitations. Project-relative/redacted paths and commands; no secrets, credentials, customer/production data, private paths, auth headers, or raw unbounded sensitive output.

**References:** domain-and-boundaries (DIP, entity/value/domain-service, aggregate roots, repo ports, seam vocabulary, composition-over-inheritance, CRUD carve-out); services-and-events (service layer, UoW, message bus, commands vs events, external integration, CQRS reads, DI/bootstrap, validation layering); enforcement-and-report (folder layout, import-linter snippets, structural greps, bootstrap recipe, test-pyramid gates, redacted report template).

**Helper `scan_architecture.py`:** stdin JSON `{files: [{path, content}], max_findings}` → stdout JSON `{findings, truncated, summary}`; AST-only detection of infra imports in `domain/`-like paths (`sqlalchemy`, `django`, `flask`, `fastapi`, `requests`, `redis`, `smtplib`), `session/commit/query` outside UoW/adapters, `mock.patch` of owned ports in handler tests, `Base`/`models.Model` subclasses in domain, handler→handler direct calls; deterministic ordering, early cap, never materializes unbounded output; `--help`; exit `2` + concise stderr on malformed input; no subprocess/network/filesystem-mutation/project imports.

**Evals `cases.yaml`:** fixtures with `id`, `prompt`, `kind`, `expected` (concrete strings/booleans); at least positive activation (layered review + proposal), near-miss (behavior-test-only or refactor-the-code request → redirect/scope refusal), forward-looking gate (CRUD carve-out vs Part 2 trigger), safety (production secrets/live mutation → `requires_approval: true`), diagnosis-only (`must_not_modify_product_code: true`), and evidence cases.

## 5. Safety, privacy, and failure policy

Reuses repository rules: synthetic/local-isolated default; unconditional refusal of real secrets, live credentials, customer/production data; narrow approval only for non-sensitive live inspection; argument arrays + controlled env/timeouts; bounded redacted evidence; untrusted-data treatment for repo content, docs, logs, generated values; no `.env`/credential-store/production-DB mining for inputs; seam-gap reporting instead of silent invention; ambiguous-direction → open question; missing-tool → explicit fallback + not-run; over-budget scan → stratify/prioritize, never silent truncation; failure → minimize, retain advisory label, ask before any product change (which is out of scope).

## 6. Documentation and community files

`README.md`: new table row, install command (`npx skills add nexusnv/python-agentic-skills --skill python-architecture-review`), which-skill guidance update (review vs test vs audit vs typing split, CRUD carve-out note). `skills.sh.json`: add skill to a new or existing grouping. `CHANGELOG.md`: new version entry listing the skill, install command, read-only behavior, verification commands. `CONTRIBUTING.md`/`SECURITY.md`/`AGENTS.md`: no behavior change needed; new skill follows existing naming, frontmatter, disclosure, eval, test, and review rules.

## 7. Verification and CI

Extend existing suites (no new framework): structural tests discover the sixth skill (frontmatter name=dir, portable keys, links resolve, references/scripts exist, <500 lines, single canonical tree); quality contracts (required sections, safety/diagnosis language, seam/boundary contract, report path; eval kinds positive/near-miss/safety/evidence with approval flags); helper tests (deterministic, respects limit + `truncated`, preserves ordering, `--help`, rejects malformed with exit 2, no execution/network imports). CI already runs `ruff`, `pytest`, `skills-ref validate` per skill, `git diff --check`, and skills.sh discovery smoke — add the new skill path to the validate + smoke steps. Completion requires fresh command output and exit status; green targeted tests are not architecture-fitness proof; semantic evals remain maintainer fixtures, not LLM-pass claims.

## 8. Non-goals for v1

- No product-code refactoring, scaffolding writes beyond an explicitly requested proposal file, or migration execution (strangler/event-interception roadmap may be described, not executed).
- No required Django/SQLAlchemy/Flask/import-linter/Hypothesis/Docker/hosted-service dependency.
- No production credentials, live-service calls, or destructive operations by default.
- No exhaustive fitness proof from a static scan.
- No duplicate skill tree; no PyPI package or runner replacement.

## 9. Success criteria

1. skills.sh discovers the new skill from a clean checkout and installs it independently.
2. Agent Skills validator accepts the new skill directory.
3. CI and local tests pass on the supported Python matrix.
4. A new agent can run the skill without reading the research report.
5. A skill run produces chat findings plus (on request) a reproducible proposal/guards report with gate evidence and honest limits.
6. Safety eval fixtures cover live/destructive/secret-bearing behavior for future semantic evaluation.
7. Review vs test vs audit vs typing activation boundary is unambiguous in README + SKILL descriptions + evals.
8. The skill demonstrably avoids over-prescribing: CRUD targets get the carve-out with reasons; Part 2 appears only with trigger evidence.

## References

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices)
- [skills.sh CLI reference](https://www.skills.sh/docs/cli)
- [Cosmic Python — free online edition](https://www.cosmicpython.com/book/preface.html)
- [Cosmic Python code](https://github.com/cosmicpython/code)
- [Research report in this repo](../../research/2026-10-09-cosmic-python-architecture-patterns.md)
