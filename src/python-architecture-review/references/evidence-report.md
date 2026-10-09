# Enforcement guards and proposal report template

Use this reference before writing guards and again before finishing. It gives the enforceable folder hierarchy, dependency rules, and test gates, then the copyable proposal template. Static scanner findings are advisory until confirmed by reading code.

## Canonical folder hierarchy

```text
src/<pkg>/
  domain/{model.py, events.py, commands.py, exceptions.py}
  service_layer/{handlers.py, messagebus.py, unit_of_work.py}
  adapters/{orm.py, repository.py, notifications.py, redis_eventpublisher.py, ...}
  entrypoints/{flask_app.py, redis_eventconsumer.py, ...}
  bootstrap.py
  config.py
  views.py
tests/{unit/, integration/, e2e/} + conftest.py
```

Rules: `domain/` holds pure business logic; `service_layer/` holds use cases plus the unit of work; `adapters/` holds secondary (driven) I/O with ports co-located; `entrypoints/` holds primary (driving) thin translators that build commands or events and call `bus.handle`; `bootstrap.py` is the sole production importer of config plus concrete adapters; `views.py` holds reads and never mutates aggregates.

## Import rules (import-linter snippets)

```ini
[importlinter]
root_package = src.<pkg>

[[importlinter.contracts]]
name = domain-independence
type = forbidden
source_modules = src.<pkg>.domain
forbidden_modules = src.<pkg>.adapters, src.<pkg>.entrypoints, src.<pkg>.config

[[importlinter.contracts]]
name = service-depends-on-abstractions
type = forbidden
source_modules = src.<pkg>.service_layer
forbidden_modules = sqlalchemy, django, flask, fastapi, redis, requests
```

Entrypoints reach the domain only via commands and events, never by importing `domain.model` for mutation. Repositories expose only aggregate roots.

## Structural greps

```bash
rg -n 'session\.(commit|query|add)' --glob '!*unit_of_work*' --glob '!adapters/*' src/
rg -n 'send_mail|SMTP|redis\.publish|requests\.' --glob '!adapters/*' --glob '!bootstrap.py' src/
rg -n 'class \w+\((Base|Model|DeclarativeBase)\)' src/*/domain/
rg -n 'mock\.patch(\.object)?\(.*(Repository|UnitOfWork|MessageBus|Notifications)' tests/
rg -n 'mocker\.patch(\.object)?\(.*(Repository|UnitOfWork|MessageBus|Notifications)' tests/
rg -n '(^|[^\w.])patch(\.object)?\(.*(Repository|UnitOfWork|MessageBus|Notifications)' tests/
```

Each hit is advisory; confirm by reading code, then grade at most Minor until confirmed.
Scanner severity `advisory` maps to report severity Minor with confirmed set to no.
The scanner matches `session.commit/query/add` only on a literal `session` receiver
(`session`, `self.session`, `db.session`) and matches `patch` in all three mock
spellings including the `.object(...)` form, including calls split across lines.

## Bootstrap recipe

`bootstrap.py::bootstrap(start_orm, uow, notifications, publish) -> MessageBus`: run init (`orm.start_mappers()`, logging), build the dependency dict, pre-bind handler dependencies (partial, closure, or handler class), return `MessageBus(uow, event_handlers, command_handlers)`. Entrypoints do no construction. Tests override with `FakeUnitOfWork`, fake notifications, and noop publishers.

## Transaction, aggregate, validation, pyramid gates

- Only the unit of work provides repo access plus `commit()`/`rollback()`; handlers use `with uow:` plus explicit `commit()`; entrypoints never commit.
- One aggregate per repository and per transaction; cross-aggregate work chains via events.
- Validation outward to inward: tolerant message shape at the edge, preconditions in service, business rules in domain.
- Pyramid: one happy plus one unhappy end-to-end test per feature; bulk handler tests with fakes; small deletable domain core; view tests via the bus; concurrency tests for contended aggregates.

Use `scripts/scan_architecture.py` only to scan supplied source for advisory layer patterns. It is a static analyzer, never a target executor, and reads file content supplied on stdin.

Record commands and working directories as project-relative or explicitly redacted. **Unconditionally refuse real secrets, live credentials, customer data, and production data.** Approval may permit only a narrowly scoped, non-sensitive live inspection; approval never authorizes secret or data access. Never persist, display, or forward those values, private paths, authorization headers, or raw unbounded sensitive output. Static findings are advisory until confirmed by execution or independent review.

```markdown
# Architecture review proposal

## Scope

- Review target or module boundary:
- Consumer and direction:
- Forward-looking sources:
- Seam dimensions:
- Complexity gate and depth:
- Coverage areas/plan:
- Review profile: quick / deep

## Runner and environment

- Project-native runner and version:
- Working directory (project-relative or redacted):
- Environment fingerprint (runtime, OS, locale, timezone, and non-sensitive settings):
- Scanner version and command (or N/A with reason):
- Seed and generator (or N/A with reason):
- Approval status for permitted non-sensitive live, destructive, or cost-incurring work:
- Synthetic data and isolation:
- Report date:

## Findings

| finding_id | severity | dimension | location | evidence | risk_if_ignored | proposed_remediation | confirmed |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | Critical / Major / Minor |  |  |  |  |  | yes / no |

The Findings table states one row per advisory or confirmed issue. Cap unconfirmed static patterns at Minor with confirmed set to no.

## Exact executions

| execution_id | case_ids | working directory (project-relative or redacted) | exact command (redacted, structure preserved) | replay note | exit status | runner | environment | bounded evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution-001 |  |  |  |  |  |  |  |  |

Record one row for every command and retry. Keep exit status exact. For a safe command, provide the exact replay form. For an unsafe or secret-bearing form, preserve structure with a documented redaction marker and explain the omission; never record the secret value.

## Results

| case_id | execution_id | result state | observed outcome | oracle result | evidence reference | retry of | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | pass / fail / skip / expected-failure |  |  |  |  |  |

Use only executed rows here. Put blocked or not-run work in the Not run and skips table.

## Not run and skips

| case id or coverage area | result state | reason | command | exit status | coverage impact |
| --- | --- | --- | --- | --- | --- |
|  | not-run / skip / expected-failure |  | N/A or exact bounded command | N/A or exact status |  |

Record skipped, expected-failure, unavailable, blocked, and otherwise not-run work explicitly. Never convert an absent command or an approval block into a pass.

## Safety and privacy

- Synthetic data used:
- Approval never authorized secret or data access: yes / no

## Limitations and conclusion

- What the review establishes:
- What the review does not establish:
- Coverage gaps and discarded/truncated families:
- Follow-up or diagnosis-only next steps:
- Overall result: pass / fail / partial / blocked
- Product-code change remains pending separate approval: yes / no
```

A report can be partial or failing when that status is explicit. Do not omit failures, retries, truncation, skips, not-run work, limitations, or the boundary between static patterns and confirmed findings. Save the report using the target repository's convention or at `architecture-reviews/<descriptive-name>.md`.
