# Cosmic Python (Architecture Patterns with Python) — Architecture Research

**Book:** *Architecture Patterns with Python* by Harry Percival and Bob Gregory (O'Reilly, 2020).
**Free online edition:** https://www.cosmicpython.com / https://www.cosmicpython.com/book/preface.html
**Code:** https://github.com/cosmicpython/code (per-chapter branches)
**License of online edition/code:** CC BY-NC-ND (https://www.cosmicpython.com/book/preface.html)
**Research date:** 2026-10-09. All claims verified against primary sources (book chapters) listed per section, not secondary write-ups.
**Context:** MADE.com furniture e-commerce allocation domain (allocate order lines to batches of stock) is the running example throughout.

> Scope: this report summarizes *what the book actually prescribes* — patterns, dependency rules, testing guidance, folder layout, enforcement mechanisms, anti-patterns — so that a later agentic review skill can guard the same boundaries. It does **not** create the skill.

---

## 1. Part structure and full chapter list

Source: https://www.cosmicpython.com/book/preface.html (overview of Parts 1/2 + additional content), TOC on every chapter page.

- **Preface** — https://www.cosmicpython.com/book/preface.html — motivation (TDD + DDD + event-driven), audience, how to code along (per-chapter Git branches), CC license.
- **Introduction** — https://www.cosmicpython.com/book/introduction.html — Big Ball of Mud, encapsulation/abstraction, layered architecture, Dependency Inversion Principle (DIP), preview of Domain Model.
- **Part 1: Building an Architecture to Support Domain Modeling** — https://www.cosmicpython.com/book/part1.html
  - **Ch 1 Domain Modeling** — https://www.cosmicpython.com/book/chapter_01_domain_model.html — Entity, Value Object, Domain Service, domain exceptions.
  - **Ch 2 Repository Pattern** — https://www.cosmicpython.com/book/chapter_02_repository.html — persistence ignorance, ORM depends on model, `AbstractRepository`, fake repo.
  - **Ch 3 Interlude: On Coupling and Abstractions** — https://www.cosmicpython.com/book/chapter_03_abstractions.html — Functional Core / Imperative Shell, choosing abstractions, fakes vs mocks, edge-to-edge testing, DI without ABCs.
  - **Ch 4 Service Layer** — https://www.cosmicpython.com/book/chapter_04_service_layer.html — orchestration/use-case layer, primitive parameters, folder layout (`domain/`, `service_layer/`, `adapters/`, `entrypoints/`).
  - **Ch 5 TDD in High Gear and Low Gear** — https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear.html — test pyramid, high-gear (service) vs low-gear (domain) testing, `add_batch` service to decouple tests.
  - **Ch 6 Unit of Work Pattern** — https://www.cosmicpython.com/book/chapter_06_uow.html — atomic operations, context manager, explicit commit, `FakeUnitOfWork`, "don't mock what you don't own".
  - **Ch 7 Aggregates and Consistency Boundaries** — https://www.cosmicpython.com/book/chapter_07_aggregate.html — `Product` aggregate wrapping `Batch`, one-aggregate-per-repo rule, optimistic concurrency with `version_number`, Part 1 recap diagram.
- **Part 2: Event-Driven Architecture** — https://www.cosmicpython.com/book/part2.html
  - **Ch 8 Events and the Message Bus** — https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html — Domain Events, message bus dict, 3 options for raising/collecting events (service collects / service raises / UoW collects via `seen` + `collect_new_events`).
  - **Ch 9 Going to Town on the Message Bus** — https://www.cosmicpython.com/book/chapter_09_all_messagebus.html — everything-is-a-handler refactor, `BatchQuantityChanged` → `AllocationRequired` chain, bus-internal queue, fake message bus for isolated handler tests.
  - **Ch 10 Commands and Command Handler** — https://www.cosmicpython.com/book/chapter_10_commands.html — Command vs Event table, `COMMAND_HANDLERS` (1:1) vs `EVENT_HANDLERS` (1:N), fail-noisily vs fail-independently, retries with tenacity.
  - **Ch 11 External Events / Microservices Integration** — https://www.cosmicpython.com/book/chapter_11_external_events.html — temporal decoupling, Redis pub/sub `redis_eventconsumer.py` / `redis_eventpublisher.py`, internal vs external events, noun-vs-verb service split, connascence.
  - **Ch 12 CQRS** — https://www.cosmicpython.com/book/chapter_12_cqrs.html — CQS / Post-Redirect-Get, `views.py` with raw SQL, read-model options table, event-driven read-model updates (incl. Redis read model), `GET /allocations/<orderid>` after `POST → 202`.
  - **Ch 13 Dependency Injection (and Bootstrapping)** — https://www.cosmicpython.com/book/chapter_13_dependency_injection.html — implicit vs explicit deps, bootstrap/composition root, `functools.partial` vs closures vs handler classes, `inspect.signature` injection, `MessageBus` as class, `AbstractNotifications` worked example with fakes + MailHog integration test.
- **Epilogue** — https://www.cosmicpython.com/book/epilogue_1_how_to_get_there_from_here.html — strangler/event-interception migration, separating entangled responsibilities, identifying aggregates (IDs not object refs), footguns (reliable messaging, idempotency, schema versioning), reviewer Q&A.
- **Appendix A: Summary Diagram and Table** — https://www.cosmicpython.com/book/appendix_ds1_table.html — canonical component table (Domain / Service Layer / Adapters / Entrypoints / external bus).
- **Appendix B: Template Project Structure** — https://www.cosmicpython.com/book/appendix_project_structure.html — `src/<pkg>/`, `config.py`, Dockerfile/docker-compose, `tests/{unit,integration,e2e}/` layout.
- **Appendix C: Swapping Infrastructure (CSVs)** — https://www.cosmicpython.com/book/appendix_csvs.html — `CsvRepository` + `CsvUnitOfWork` proof that service/domain are storage-agnostic.
- **Appendix D: Repository + UoW with Django** — https://www.cosmicpython.com/book/appendix_django.html — Django adaptation (`DjangoRepository`, `DjangoUnitOfWork`, `update_from_domain`/`to_domain`, `transaction.set_autocommit(False)`), fat-models warning.
- **Appendix E: Validation** — https://www.cosmicpython.com/book/appendix_validation.html — syntax/semantics/pragmatics split, Tolerant Reader, `ensure.py` preconditions, `SkipMessage`, bus-level validation.

---

## 2. Core patterns (what the book actually says)

### 2.1 Dependency Inversion Principle (DIP) — the through-line

- Source: https://www.cosmicpython.com/book/introduction.html (`#dip`) + applied in Ch 2 (https://www.cosmicpython.com/book/chapter_02_repository.html), Ch 4 (https://www.cosmicpython.com/book/chapter_04_service_layer.html), Ch 6 (https://www.cosmicpython.com/book/chapter_06_uow.html).
- Formal definition quoted: (1) high-level modules should not depend on low-level modules; both should depend on abstractions. (2) Abstractions should not depend on details; details should depend on abstractions.
- High-level = business concepts (patients/trials, trades, allocation); low-level = filesystem, SMTP, HTTP, AMQP. Goal: change each independently.
- Every later pattern is presented as a worked DIP example: ORM imports model (not vice versa); service depends on `AbstractRepository`/`AbstractUnitOfWork`; handlers depend on abstract notifications/publisher.

### 2.2 Ports & Adapters / Hexagonal / Onion / Clean — treated as one idea

- Source: https://www.cosmicpython.com/book/chapter_02_repository.html ("Is This Ports and Adapters?", "What Is a Port and What Is an Adapter, in Python?").
- Book explicitly says: ports & adapters ≈ hexagonal ≈ onion ≈ clean; "all boil down to DIP". Does not nitpick differences; cites Mark Seemann post.
- Python mapping given: **port** = interface between app and abstracted thing (`AbstractRepository`; or if no ABC, the duck-type: method names + arg names/types). **Adapter** = implementation (`SqlAlchemyRepository`, `FakeRepository`, `CsvRepository`, Flask app, Redis consumer/publisher, Django views).
- Primary/driving/outward-facing adapters = entrypoints (`entrypoints/`); secondary/driven/inward-facing adapters = `adapters/` (repo, ORM, redis, email/notifications). Source: Ch 4 folder section (https://www.cosmicpython.com/book/chapter_04_service_layer.html) + Appendix A (https://www.cosmicpython.com/book/appendix_ds1_table.html).
- Onion/layered diagrams (Ch 2): domain at center/inside, dependencies point inward; presentation and DB both depend inward.

### 2.3 Domain Model (Ch 1) — Entity, Value Object, Domain Service, exceptions

- Source: https://www.cosmicpython.com/book/chapter_01_domain_model.html.
- Domain model = business-logic layer renamed in DDD vocabulary; built from ubiquitous-language conversations (allocation glossary: product/SKU, order/order lines, batch/reference/ETA, allocate, available quantity, out-of-stock).
- **Value Object** (`OrderLine`, `Name`, `Money` examples): identified only by data, immutable (`@dataclass(frozen=True)` / `NamedTuple`), value equality; behavior OK (e.g. `Money.__add__` with currency check). Tests show equality + math operators.
- **Entity** (`Batch`, `Person` example): long-lived identity (`reference`), mutable attributes, identity equality (`__eq__`/`__hash__` on `reference`); warning to change `__eq__`+`__hash__` together, link to Hynek Schlawack "Python Hashes and Equality".
- **Domain Service** (`allocate(line, batches) -> str` function): Evans quote "Sometimes, it just isn't a thing"; stateless operation with no natural entity home. Distinct from service-layer (application) service — see §2.5.
- Python idioms: `sorted(batches)` via `Batch.__gt__` on ETA (None = in-stock sorts first); domain exceptions (`OutOfStock`) named in ubiquitous language. Later (Ch 8) the book calls raising `OutOfStock` for control flow a smell and replaces it with events.
- Recap rules: keep model dependency-free; distinguish entity/value; verbs can be functions (`manage_foo()` over `FooManager`); apply SOLID/composition-over-inheritance here; defer consistency boundaries to Ch 7.
- Explicit non-goal: "This Is Not a DDD Book" — points to Evans blue book and Vernon red book.

### 2.4 Repository (Ch 2)

- Source: https://www.cosmicpython.com/book/chapter_02_repository.html.
- Definition: abstraction over persistent storage; "pretend all data is in memory" (`add()` + `get()`; `list()` added pragmatically; `delete`/`update` deliberately omitted — soft-delete via `batch.cancel()`, updates via UoW).
- **Persistence ignorance via classical mapping:** "normal" declarative ORM (model inherits `Base`/`models.Model`) is condemned as model-depends-on-ORM. Prescription: separate `Table` definitions + `mapper(model.OrderLine, order_lines)` in `orm.py::start_mappers()` so ORM imports model. Django has no classical-mapper equivalent → manual `to_domain()`/`update_from_domain()` translation layer (Appendix D).
- ABC example: `AbstractRepository(add, get)` with `@abc.abstractmethod`; didactic use only — book notes teams often delete ABCs and rely on duck typing; points to PEP 544 `Protocol` as alternative.
- Concrete: `SqlAlchemyRepository(session)` (`add→session.add`, `get→query...one()`, `list→query...all()`); `commit()` deliberately left to caller (foreshadows UoW).
- **Fake:** `FakeRepository` wrapping a `set` with one-line methods; design-feedback heuristic: "if it's hard to fake, the abstraction is too complicated".
- Trade-offs table (Ch 2): pros = simple storage↔domain interface, fakeability, model-first focus, full schema control; cons = ORM already decouples DB-vendor swap, hand-maintained mappings cost, extra indirection/"WTF factor". Explicit carve-out: "If your app is just CRUD, you don't need a domain model or repository."

### 2.5 Service Layer (Ch 4)

- Source: https://www.cosmicpython.com/book/chapter_04_service_layer.html.
- Definition: orchestration/use-case layer between entrypoints and domain. Typical steps: fetch from repo → checks/assertions vs current state → call domain service → persist.
- Example evolution: Flask `allocate_endpoint` grows `is_valid_sku` + `try/except OutOfStock` + `session.commit()` → extracted to `services.allocate(line, repo, session)` raising `InvalidSku`; Flask left with only web concerns (per-request session, JSON parsing, status codes).
- **Depend on abstractions:** `allocate(..., repo: AbstractRepository, ...)` works with `FakeRepository` in tests and `SqlAlchemyRepository` at runtime (three DIP diagrams: abstract deps / test deps / runtime deps incl. ORM→DB).
- **Primitive parameters (Ch 5 completes this):** Ch 4 introduces; Ch 5 (https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear.html) mandates `allocate(orderid, sku, qty, ...)` over `allocate(OrderLine, ...)` + `add_batch` service so service tests need no domain imports (or isolate domain use to fixtures/factories like `FakeRepository.for_batch`).
- **Domain service vs application service** (Ch 4 sidebar "Why Is Everything Called a Service?"): domain service = business concept (e.g. `calculate_tax`, `allocate`); application/service-layer service = use-case orchestration (fetch, validate, persist).
- Trade-offs: pros = single use-case catalogue, refactorable domain behind API, thin adapters, high-gear testing; cons = overkill for pure-web apps (controllers suffice), another abstraction, anemic-domain risk if logic leaks up, fat-models+thin-controllers as lighter alternative. Tip: read-only `repo.get()` directly in handler is fine; CQRS (Ch 12) revisits reads.

### 2.6 Unit of Work (Ch 6)

- Source: https://www.cosmicpython.com/book/chapter_06_uow.html.
- Definition: abstraction over *atomic operations*; collaborator with Repository; provides snapshot isolation, all-at-once persistence, single persistence API + repo access (`uow.batches`).
- API: `AbstractUnitOfWork` with `.batches`, context-manager protocol (`__enter__`/`__exit__` → `rollback()` by default), abstract `commit()`/`rollback()`. Concrete `SqlAlchemyUnitOfWork(session_factory)` builds session + `SqlAlchemyRepository` in `__enter__`, closes in `__exit__`, delegates commit/rollback. `DEFAULT_SESSION_FACTORY` overridable (Postgres default, SQLite in integration tests).
- Service shape after UoW: `def allocate(orderid, sku, qty, uow: AbstractUnitOfWork)` with `with uow: ... uow.commit()`.
- **Fake:** `FakeUnitOfWork` (owns `FakeRepository([])`, `committed` flag, no-op rollback). Rationale "Don't mock what you don't own": fake our thin UoW, not SQLAlchemy `Session`, to narrow the interface and limit data-access sprawl.
- **Explicit commit preferred over implicit-commit-on-exit:** safe-by-default (only explicit `commit()` mutates); all other exits roll back. Alternative `@contextmanager`/composition variants offered as exercise.
- Grouping examples: `reallocate` (deallocate+allocate atomically), `change_batch_quantity` (loop `deallocate_one()` while negative, single commit).
- Test hygiene: `test_orm.py` was a learning scaffold → discard long-term; keep `test_repository.py`/`test_uow.py` only where mapping/transaction behavior is nontrivial; rollback-behavior tests (`rolls_back_uncommitted`, `rolls_back_on_error`); transaction tests should run against real engine where semantics matter.
- Trade-offs: pros = visual atomic blocks, safe defaults, repo access point, later carries events; cons = ORM already has sessions/context managers, must think about nesting/threads/rollback, Django/Flask-SQLAlchemy defaults may suffice. Quotes SQLAlchemy docs ("keep session/transaction lifecycle separate and external").

### 2.7 Aggregate (Ch 7)

- Source: https://www.cosmicpython.com/book/chapter_07_aggregate.html.
- Motivation: invariants (e.g. "line allocated to ≤1 batch", "available ≥ 0") + concurrency (can't lock whole `batches` table at 10k orders/hour). Aggregate = cluster treated as unit for data changes; root is sole entrypoint; defines consistency boundary.
- Choice for allocation: **`Product(sku, batches, version_number=0)`** wrapping same-SKU `Batch`es; `allocate()` moves from domain-service function to `Product.allocate()` method. Rejected finer/coarser boundaries (`Shipment`, `Warehouse`) for wrong granularity; notes bounded contexts (allocation-`Product` ≠ ecommerce-`Product`) with Fowler bounded-context link + Vernon effective-aggregate-design papers.
- **Rule: one aggregate = one repository.** Only aggregates are publicly accessible; switch `BatchRepository` → `ProductRepository` (`add`/`get(sku)` + later `get_by_batchref` in Ch 9). "Repositories should only return aggregates" is the enforcement point.
- Performance stance: load whole aggregate in one query (tens of batches, strings/ints — ms-scale); lazy-load or re-slice aggregate (region/warehouse) if it grows to thousands; aggregates are a performance + conceptual tool, no single correct answer.
- **Optimistic concurrency:** `version_number` incremented in `Product.allocate()`; Postgres `REPEATABLE READ` (or `SELECT ... FOR UPDATE` pessimistic alternative shown) makes second concurrent committer fail ("could not serialize access due to concurrent update"); retry from scratch (Ch 10 elaborates). Thread+`sleep(0.2)` integration test asserts version bumped once, one allocation wins. Notes version needn't live in domain (service/UoW options considered) but domain placement chosen as cleanest; UUID-that-changes-on-write equivalent.
- Trade-offs: pros = public/private class discipline, ORM perf via explicit boundaries, single-owner state changes; cons = new concept load (entity/value/aggregate), one-aggregate-per-txn mental shift, eventual consistency complexity. Part 1 recap diagram + "simple CRUD → just use Django" carve-out repeated.

### 2.8 Domain Events + Message Bus (Ch 8–9)

- Source: Ch 8 https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html; Ch 9 https://www.cosmicpython.com/book/chapter_09_all_messagebus.html.
- Trigger: `OutOfStock → notify buying team` side effect; naive placements (Flask controller, `Product.allocate` calling `email.send_mail`, service `try/except`+re-raise) each violate SRP ("can't describe fn without 'then/and'").
- **Events:** value-object dataclasses in `domain/events.py` (`class Event`, `@dataclass OutOfStock(sku)`); raised by recording on `aggregate.events: List[Event]`, not by sending. Ch 8 converts `allocate` to return `None` + append `OutOfStock` instead of raising.
- **Message bus:** dict `HANDLERS[type(event)] -> [handlers]`; `send_out_of_stock_notification(event)` adapter. Explicitly synchronous, single-threaded; Celery contrasted (bus ≈ Express/UI loop/actor, not task queue; background work → external events, Ch 11).
- Three wiring options compared:
  1. Service collects `product.events` → `messagebus.handle(...)` (explicit, repetitive).
  2. Service raises its own events (some production systems do this).
  3. **Preferred:** UoW auto-collects via `repository.seen: Set[Product]` (`add`/`get` record; subclasses implement `_add`/`_get`) + `collect_new_events()` generator; service stays clean. Composition-over-inheritance `TrackingRepository` wrapper offered as exercise to avoid `_`-methods; ABC→`Protocol` suggested.
- Ch 9 makes bus the **main entrypoint**: `services.py` → `handlers.py` with `(event, uow)` signatures; input events `BatchCreated`/`AllocationRequired` (+ later `BatchQuantityChanged`); `messagebus.handle(event, uow)` owns FIFO `queue`, extends from `uow.collect_new_events()` after each handler; Flask builds event → `bus.handle(...)`. Temporary wart: bus returns `results` list so API can read `batchref` (fixed by CQRS Ch 12).
- New-requirement proof: `change_batch_quantity(event, uow)` → `product.change_batch_quantity` → `Batch.deallocate_one()` loop appending `AllocationRequired` events → existing `allocate` handler reallocates in separate UoWs (sequence diagram; warning: two transactions → need failure monitoring). `get_by_batchref` repo query added with "single-aggregate queries OK, `get_most_popular_products`-style queries are a smell" rule.
- Handler-test isolation option: `FakeUnitOfWorkWithFakeMessageBus(events_published=[...])` or class-based `AbstractMessageBus`/`FakeMessageBus`; default to edge-to-edge, isolate only when chains get complex.
- Trade-offs (Ch 8 + Ch 9): pros = SRP, swappable side effects, business-language events, new requirement = new events/handlers/adapters with no architectural change; cons = magic (`commit` sending email), synchronous-handler latency, no single place showing full flow, circular-handler/infinite-loop risk, web-unpredictability, event/model field duplication.

### 2.9 Commands (Ch 10)

- Source: https://www.cosmicpython.com/book/chapter_10_commands.html.
- Distinction table: Event = past tense, broadcast to all listeners, fail independently; Command = imperative (`Allocate`, `CreateBatch`, `ChangeBatchQuantity` in `domain/commands.py`), sent to one recipient, fail noisily (raise to caller).
- Bus split: `handle(message)` dispatches to `handle_event` (loops `EVENT_HANDLERS[t]`, try/except+log+`continue`, optional tenacity retry 3× exponential) vs `handle_command` (single `COMMAND_HANDLERS[t]` lookup, exception re-raised). `Message = Union[Command, Event]`.
- Design rationale (VIP/history example): command handler modifies one aggregate atomically; follow-on bookkeeping via events that may fail independently — improves reliability (busy email server must not block order-taking; buggy VIP rule must not block payment). Align txn boundaries to business-process steps.
- Recovery: structured log lines (`handling event X with handler Y`, dataclass reprs pasteable into shell) + replay; tenacity retries; warning that giving up eventually is unavoidable (epilogue pointers). Idempotency deferred to epilogue.

### 2.10 Event-driven microservices integration (Ch 11)

- Source: https://www.cosmicpython.com/book/chapter_11_external_events.html.
- Anti-model: noun-per-service CRUD-over-HTTP (`Orders`→`Batches`→`Warehouse` + reverse `Warehouse`→`Batches`→`Orders`) = distributed ball of mud; temporal coupling + connascence of execution/timing (cites connascence.io).
- Prescription: verb-oriented services as consistency boundaries; async messaging (Redis pub/sub in book; EventStore/Kafka/RabbitMQ in production) replacing synchronous RPC; agree only on event names/fields (connascence of name).
- Concrete: `entrypoints/redis_eventconsumer.py` (subscribe `change_batch_quantity` → JSON → `ChangeBatchQuantity` command → `messagebus.handle`) mirrors Flask adapter; `adapters/redis_eventpublisher.publish(channel, event)` (`asdict(event)` → JSON); new outbound `Allocated(orderid, sku, qty, batchref)` event raised in `Product.allocate()`, published to `line_allocated` channel by `publish_allocated_event` handler. E2E test uses `subscribe_to`/`publish_message` + tenacity polling loop. Keep internal vs external events distinct; validate outbound events (Appendix E).
- Trade-offs: pros = no distributed mud, independently changeable services; cons = invisible end-to-end flows, eventual consistency, at-least/at-most-once + reliability design (Fowler "What do you mean by Event-Driven" quote).

### 2.11 CQRS (Ch 12)

- Source: https://www.cosmicpython.com/book/chapter_12_cqrs.html.
- Thesis: domain models are for writes (constraints, UoW, aggregates, events); reads have different profile (100 views/sec vs 100 orders/hour, cacheable, may be stale — "as soon as you render, data is stale" + forklift-damage parables). Table: read = simple/cacheable/eventually-consistent; write = complex/uncacheable/transactional.
- CQS fix first: POST returns `202` + `Location`-style redirect, not data; `POST /allocate → 202`, then `GET /allocations/<orderid>` from new `views.py`. Removes bus-returns-results wart.
- View options compared with trade-off table:
  1. Repository (`for_order` + `Batch.orderids` + nested loops) — consistent but clunky, Python-side filtering.
  2. ORM query (join `Batch._allocations`) — awkward SQLAlchemy, SELECT N+1 risk.
  3. **Raw SQL against normalized tables** — "just SQL", fine control; schema duplication cost.
  4. Denormalized `allocations_view(orderid, sku, batchref)` table — fastest `WHERE key=value`, scalable reads; slight write cost.
  5. **Event-updated read store** (same-DB table or Redis hash via `hset`/`hgetall`) — `Allocated → add_allocation_to_read_model`, `Deallocated → remove...`; rebuildable by replaying write side; trivially re-targetable (SQL→Redis) with identical integration tests (`test_views.py` drives setup through message bus, asserts on view).
- Guidance: split `views.py` (reads) from handlers (writes) even without full CQRS; repositories/domain reuse fine for same-concept reads; reach for denormalized/event-driven read models as richness/perf diverge. Notes MADE.com uses Redis + Varnish in production but the book example likely only needs raw SQL.

### 2.12 Explicit dependencies + Bootstrap/DI (Ch 13)

- Source: https://www.cosmicpython.com/book/chapter_13_dependency_injection.html.
- Contrast: UoW/session-factory are explicit (constructor args, overridable in tests) vs email/redis as implicit imports + `mock.patch("allocation.adapters.email.send")`. Mock critique: per-test boilerplate, implementation coupling (`import email` vs `from email import send_mail` breaks mocks).
- Prescription: make side-effect deps explicit (`send_out_of_stock_notification(event, send_mail: Callable)`), inject once in **bootstrap/composition root** (`bootstrap.py::bootstrap(start_orm, uow, send_mail/notifications, publish) -> MessageBus`): does init (`orm.start_mappers()`, logging), builds `dependencies` dict, returns configured `MessageBus(uow, event_handlers, command_handlers)`.
- Injection styles: closures/lambdas, `functools.partial` (nicer stack traces; beware late-binding), or handler classes (`__init__(deps)` + `__call__(message)`). `inspect.signature`-based `inject_dependencies(handler, deps)` vs fully-manual lambda map (both presented; manual deemed viable). Real DI frameworks (`Inject`, `punq`, `dependencies`) only if chained/multi-level DI emerges.
- `MessageBus` becomes a class holding injected handlers + `uow`; `handle/handle_event/handle_command` move to methods; handlers take only `message` (deps pre-bound). Entrypoints shrink to `bus = bootstrap.bootstrap(); bus.handle(cmd)`; tests get `bootstrap(..., uow=FakeUnitOfWork()/sqlite UoW, send_mail/publish=noops)`. Note: bus-on-Flask-module-global isn't thread-safe; Flask app factories suggested.
- "Proper adapter" recipe (notifications example): ABC (`AbstractNotifications.send`) → concrete (`EmailNotifications(smtplib)`) → fake (`FakeNotifications.sent defaultdict`) for unit tests → less-fake real (MailHog in docker-compose, `test_email.py` asserting From/To/Data) for integration. Steps summarized as: API-via-ABC → real → fake → docker-real → test-real → profit.

### 2.13 Folder structure prescriptions

- Source: Ch 4 https://www.cosmicpython.com/book/chapter_04_service_layer.html ("Putting Things in Folders") + Appendix B https://www.cosmicpython.com/book/appendix_project_structure.html + Appendix A https://www.cosmicpython.com/book/appendix_ds1_table.html.
- Canonical layout (evolved through book):
  ```
  src/<pkg>/
    domain/{model.py, events.py, commands.py, exceptions.py}
    service_layer/{handlers.py (was services.py), unit_of_work.py, messagebus.py}
    adapters/{orm.py, repository.py, redis_eventpublisher.py, notifications.py/email.py, ...}
    entrypoints/{flask_app.py, redis_eventconsumer.py, ...}
    bootstrap.py
    config.py
  tests/{unit/,integration/,e2e/} + conftest.py + pytest.ini
  Dockerfile + docker-compose.yml + Makefile + requirements.txt + src/setup.py
  ```
- Rules: `domain/` = pure business logic (later `commands.py`/`events.py` join `model.py`); `service_layer/` = use cases + UoW; `adapters/` = secondary/driven I/O; `entrypoints/` = primary/driving adapters (Flask, Redis consumer, CLI/CSV, tests-as-adapter); ports (ABCs/`Protocol`s) live beside their adapters.
- Config: `config.py` functions reading `os.environ` with localhost defaults (`get_postgres_uri`, `get_api_url`, `get_redis_host_and_port`, `get_email_host_and_port`); 12-factor env vars; keep config out of global import-time constants; only bootstrap + tests import config (Ch 13 tip). Docker: one main image for code, infra services (postgres/redis/mailhog), env/hostname/port mapping inside vs outside cluster, volume mounts + `PYTHONDONTWRITEBYTECODE`, `pip install -e /src` via `setup.py`.

### 2.14 Test pyramid with architecture (unit / integration / e2e)

- Source: Ch 4 https://www.cosmicpython.com/book/chapter_04_service_layer.html, Ch 5 https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear.html, plus Ch 3 https://www.cosmicpython.com/book/chapter_03_abstractions.html and Ch 6 https://www.cosmicpython.com/book/chapter_06_uow.html.
- Counts cited mid-book: 15 unit / 8 integration / 2 e2e ("healthy pyramid").
- Rules of thumb (Ch 5 "Recap"):
  - **1 e2e per feature** (e.g. HTTP API happy path + one unhappy-path test covering all error bubbling); proves wiring.
  - **Bulk in service/handler (edge-to-edge) tests** with fakes for I/O; exhaustively cover branches/edge cases; fastest broad coverage.
  - **Small core of domain tests** for design feedback + living docs; delete when covered above to avoid glue.
  - Error handling counts as a feature.
- High gear vs low gear: high = service/handler tests (low coupling, high coverage, faster feature work); low = domain tests (high feedback, executable docs, use when starting out or stuck on gnarly design). Spectrum diagram: API → service → domain = decreasing coverage/increasing feedback + change-barrier.
- Enablers: `FakeRepository`/`FakeUnitOfWork`/fake bus/notifications; primitive/event/command APIs so tests avoid domain imports; `add_batch` service + `POST /add_batch` endpoint so E2E avoids raw-SQL fixtures; message-bus-driven view tests.
- Ch 3 specifics: Functional Core (pure `determine_actions`) vs Imperative Shell (`sync` I/O); edge-to-edge via explicit `filesystem` dep + `FakeFilesystem` (fake+spy) over `mock.patch`; prefer state-based classicist TDD over interaction-based London-school mocks.

---

## 3. Dependency rules (what may depend on what)

Consolidated from Ch 2/4/6/7/8/12/13 + Appendix A (https://www.cosmicpython.com/book/appendix_ds1_table.html):

1. **Domain depends on nothing stateful.** Helper libs OK; ORM/web framework/DB/email/Redis not OK. ORM imports model (`import model` in `orm.py`); Django inverts via translation layer but same direction (Appendix D). Source: Ch 2 fn1 + Ch 2 classical-mapping section.
2. **Service/handlers depend on abstractions, not concretes.** `AbstractRepository` → `AbstractUnitOfWork` → (`AbstractNotifications`, publisher `Callable`/ABC). Tests inject fakes; entrypoints/bootstrap inject reals. Source: Ch 4 "Depend on Abstractions", Ch 6, Ch 13.
3. **Adapters/externals depend inward.** `SqlAlchemyRepository`/`DjangoRepository`/`CsvRepository` implement the port; ORM maps domain; Flask/Redis/CLI translate outside→commands/events and call `bus.handle`. Entrypoints do web/queue/CSV parsing + status codes only. Source: Ch 4/9/11 + App. C.
4. **UoW owns atomicity + repo access + event surfacing.** Only place that provides `.batches`/`.products`, `commit()`/`rollback()`, `collect_new_events()` from `seen` aggregates. Services/handlers never touch `session` directly. Source: Ch 6 + Ch 8 option 3.
5. **Only aggregates are reachable via repositories.** No `BatchRepository` once `Product` is the aggregate; queries must return whole aggregates (`get(sku)`, `get_by_batchref` OK; `get_most_popular_products`/`find_by_order_id` = smell → use read model). Source: Ch 7 + Ch 9.
6. **One aggregate per transaction/use case (ideal).** Cross-aggregate workflows split into separate UoWs chained by events (allocate → deallocate/reallocate; order → history → VIP email). Accept eventual consistency; never hold multi-table locks. Source: Ch 7/9/10 + epilogue tip.
7. **Reads and writes separate (CQS → CQRS as needed).** Handlers mutate via aggregates/UoW; `views.py`/read models query (SQL/Redis) without domain objects. No returning domain state from write path (POST→202→GET). Source: Ch 12.
8. **Dependencies flow to bootstrap, not through layers.** Entrypoints don't construct sessions/repos/emails; `bootstrap.py` composes `MessageBus` with injected handlers; config imported only there (+ tests). Source: Ch 13.
9. **Validation layered outward→inward.** Syntax at edge/message construction (`from_json`+schema, tolerant reader), semantics as handler preconditions (`ensure.py`, `SkipMessage`), pragmatics (stock rules) in domain. Source: Appendix E.
10. **Events flow outward, commands inward.** External bus → consumer → command → handler → aggregate → new events → internal bus → publisher/view updaters → external bus. No handler bypassing bus for cross-aggregate work. Source: Ch 9/10/11.

---

## 4. Test isolation strategies (per layer)

| Layer | Strategy (book) | Doubles used | Sources |
|---|---|---|---|
| Domain (low gear) | Pure unit tests, no I/O; ubiquitous-language names; sketch/refactor then delete when covered higher | None | Ch 1 https://www.cosmicpython.com/book/chapter_01_domain_model.html; Ch 5 |
| Service/handlers (high gear, bulk) | Edge-to-edge through `messagebus.handle(event/command, uow)` with fakes; primitives/events only, no direct domain construction (or fixture-confined) | `FakeRepository`, `FakeUnitOfWork`, `FakeNotifications`, fake `publish`, `FakeMessageBus`/`FakeUoWWithFakeMessageBus` for isolated chains | Ch 4, Ch 5 https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear.html, Ch 6, Ch 9 |
| Repository/UoW | Integration tests mixing raw SQL setup/asserts with repo/UoW calls; run txn-sensitive ones on real engine (Postgres), others may use SQLite; keep only where mapping/txn nontrivial | Real `SqlAlchemyRepository`/`SqlAlchemyUnitOfWork` + `session_factory` fixtures | Ch 2, Ch 6 https://www.cosmicpython.com/book/chapter_06_uow.html |
| Views/reads | Integration tests driving setup via message bus, asserting on view output; implementation-swappable (SQL→Redis) | Real UoW + view fns | Ch 12 https://www.cosmicpython.com/book/chapter_12_cqrs.html |
| Adapters (email/redis) | Unit with fakes; integration against less-fake dockers (MailHog, real Redis) | `FakeNotifications` vs `EmailNotifications`+MailHog | Ch 13 https://www.cosmicpython.com/book/chapter_13_dependency_injection.html |
| E2E | Minimal: 1 happy + 1 unhappy per feature over HTTP/Redis channels; helpers (`api_client`, `redis_client`, `post_to_add_batch`) replace SQL fixtures; tenacity polling for async | Real stack in Docker | Ch 4, Ch 11 https://www.cosmicpython.com/book/chapter_11_external_events.html, Ch 12 |
| Concurrency | Threads + `sleep`/semaphores asserting version/single-winner + Postgres error text | Real Postgres UoW | Ch 7 https://www.cosmicpython.com/book/chapter_07_aggregate.html |

Cross-cutting: fakes over mocks (state asserts over interaction asserts); "don't mock what you don't own"; each test file's glue cements shape — prefer fewer low-level tests.

---

## 5. Enforcement mechanisms the book actually uses

- **ABCs (didactic, optional):** `AbstractRepository`, `AbstractUnitOfWork`, `AbstractNotifications`; `@abc.abstractmethod` + `NotImplementedError`; book warns teams often delete them and rely on duck typing; suggests `pylint`/`mypy` to make ABCs bite, or PEP 544 `Protocol`s + composition (`TrackingRepository`). Sources: Ch 2 https://www.cosmicpython.com/book/chapter_02_repository.html, Ch 8, Ch 13.
- **Constructor injection + bootstrap defaults:** UoW `session_factory` param; `bootstrap(start_orm, uow, notifications/send_mail, publish)` as single override point; `inspect.signature` or manual-lambda wiring; class-handlers alternative. Source: Ch 13.
- **Repository `seen` set + `_add`/`_get` split:** mechanical enforcement that event collection sees every loaded aggregate. Source: Ch 8.
- **Aggregate-only repository rule + single-aggregate-per-UoW convention:** social/conventional, enforced by code review + handler shape (one `uow.products.get` per handler), not by linter in book. No import-linter config is given in the book — see §8 for skill opportunity. Source: Ch 7.
- **No `mock.patch` for owned abstractions:** fake owned UoW/repo/notifications/bus; reserve `patch` for truly external, unowned seams (early Ch 8 email example patched, Ch 13 replaces with injection). Source: Ch 3 https://www.cosmicpython.com/book/chapter_03_abstractions.html, Ch 6, Ch 13.
- **Test-type enforcement via layout:** `tests/unit|integration|e2e` split + `pytest.ini`/markers/fixtures (`restart_api`, `postgres_db`, `sqlite_session_factory`, `django_db(transaction=True)`); counts grepped as pyramid health check. Source: Ch 5 + App. B/D.
- **No shared-DB / no ORM-in-domain enforcement:** classical mapping direction + translation-layer pattern; CSV-swap appendix as proof test ("could you swap storage without touching domain/service?"). Source: Ch 2 + App. C/D.
- Explicitly **not** in book: import-linter (`import-linter`, `layer_linter`) rules, `__init__` re-export bans, mypy strictness gates, commit hooks. Those would be skill-added enforcement (see §8).

---

## 6. Anti-patterns the book warns about

Each sourced to the chapter that names it:

- **Big Ball of Mud / Distributed Ball of Mud** — homogeneous code where handlers know domain + email + logging; noun-per-service CRUD-over-HTTP with bidirectional RPC (Orders↔Batches↔Warehouse). Sources: Intro https://www.cosmicpython.com/book/introduction.html, Ch 11.
- **ORM-coupled domain (ActiveRecord/declarative model depends on ORM).** Ugly `Base`/`models.Model` subclasses; migration-before-test-refactor trap. Sources: Ch 2, App. D https://www.cosmicpython.com/book/appendix_django.html.
- **Fat controllers / crufty Flask app** — `is_valid_sku` + `try/except` + `session.commit()` in endpoint; fixed by service layer. Source: Ch 4.
- **Anemic Domain (too much in service layer) vs Fat Models as lighter fix.** Introduce service layer only after orchestration creeps into controllers. Source: Ch 4 trade-offs.
- **Anemic services / manager/util sprawl; model doing I/O** (`Batch` calling `email.send_mail`, model doing DB/file ops). Fixed by events + use-case extraction. Sources: Ch 8 https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html, Epilogue.
- **Exceptions for control flow** (`OutOfStock` raised for expected out-of-stock → replaced by `OutOfStock` event + `None` return). Source: Ch 8.
- **Shared database / whole-table locks / multi-aggregate transactions** — kills perf, causes deadlocks; fix via aggregates + events + eventual consistency. Sources: Ch 7, Ch 9–10.
- **Bidirectional object-graph links / dot-chaining** (`user.account.workspaces[0].documents...`) + lazy-ORM loops + SELECT N+1. Fix: IDs over refs, straight SQL/view builders, CQRS reads. Sources: Ch 12, Epilogue https://www.cosmicpython.com/book/epilogue_1_how_to_get_there_from_here.html.
- **Over-mocking / test-induced design damage debate** — `mock.patch` hiding missing abstractions, interaction asserts coupling to implementation, mocky boilerplate per test. Fix: explicit deps + fakes + state asserts. Sources: Ch 3, Ch 6, Ch 13.
- **Synchronous temporal coupling** (order-taking blocked by allocation/email/VIP-history availability). Fix: commands must succeed alone; side effects via independently-failing events + retries + monitoring/replay. Sources: Ch 10–11.
- **Primitive obsession (mindless) vs domain-object coupling** — both extremes flagged; events/commands as stable interface middle path. Source: Ch 5 + Ch 9 sidebar.
- **Overspecified validation / shared message schemas** — SKU-format policing, strict JSON-schema rejecting `COMFY-CHAISE-LONGUE` or new `ChangeBatchQuantity` fields. Fix: Tolerant Reader, `ignore_extra_keys`, opaque strings. Source: App. E https://www.cosmicpython.com/book/appendix_validation.html.
- **Inverted test pyramid / ice-cream cone** (many E2E, few unit) — fixed by service-layer + fakes. Sources: Ch 4–5.
- **Admin-bypass / CRUD-shortcut around rules** (Django admin mutating state outside handlers). Source: App. D.
- **Footguns called out as must-handle before production:** unreliable Redis pub/sub as broker, missing idempotency, missing schema versioning, no outbox/monitoring/replay. Source: Epilogue `#footguns`.

---

## 7. Concrete file-hierarchy / testing / boundary guidance usable for a review skill

This section distills *checkable* rules (each traceable above) a future skill could enforce. No skill is created here.

### 7.1 File-hierarchy checks
1. `domain/` imports only stdlib + `dataclasses`/`typing`/`datetime`/`abc` (no `sqlalchemy`, `django`, `flask`, `requests`, `redis`, `smtplib`, `os.environ`/config). Violation = infra leak into domain.
2. `service_layer/handlers.py` imports `domain.*` + `unit_of_work` ABC + adapter ABCs/`Callable`s only; never `session`, `engine`, `Flask`, `redis.Redis`, concrete repos. Takes `(command|event, uow|deps)` — never `(request, session)`.
3. `adapters/` holds all concretes (`orm.py`, `repository.py`, `redis_*.py`, `notifications.py`); ports (ABCs/`Protocol`s) co-located. `entrypoints/` holds only thin translators (Flask/Redis/CLI/CSV) + `bus.handle` call + status-code mapping.
4. `bootstrap.py` is the sole production importer of `config` + concrete adapters (outside entrypoint wiring); tests may override via `bootstrap(...)` kwargs.
5. Repositories expose only aggregate roots (`ProductRepository.get(sku)/get_by_batchref/add`); no `BatchRepository`, no `find_*`/`get_most_popular` query methods — those belong in `views.py`/read models.
6. `views.py` (reads) imports `session`/SQL/Redis-client but never mutates aggregates, never imports handlers; handlers never issue cross-aggregate queries.

### 7.2 Testing checks
7. Pyramid gate: `unit >> integration > e2e` (book's healthy point: ~15/8/2); flag new E2E that duplicates handler-covered branches; require 1-happy + 1-unhappy E2E per feature max as starting question.
8. Handler tests drive `bus.handle(command/event, fake_uow)` with primitives/events, assert state + `uow.committed` + published events — not mock interactions, not direct `Batch(...)` construction outside fixtures/factories.
9. No `mock.patch` of owned ports (repo/UoW/bus/notifications) — require fake injection via `bootstrap()`; `patch` allowed only at truly external seam with justification.
10. Integration tests required where ORM mapping or txn semantics nontrivial (allocations set mapping, rollback, version concurrency on real Postgres); ORM-learning scaffolds (`test_orm.py` style) flagged for deletion once repo tests cover them.
11. View tests set up via bus, assert on view — must pass unchanged across read-store swaps (SQL→Redis); E2E async tests must poll with bounded retry (tenacity), not fixed sleeps.
12. Concurrency: any aggregate with contention needs version/serializability test (two-txn race → single winner + defined error); multi-aggregate single-UoW updates flagged → split with events.

### 7.3 Dependency/DI checks
13. No `session.commit()`/`session.query` outside UoW; no `commit` in entrypoints; handlers use `with uow:` + explicit `uow.commit()` (safe-default rollback otherwise).
14. No direct `email.send`/`redis.publish`/`requests.*` in domain or handlers — must go through injected `Callable`/ABC dep wired in `bootstrap.py`.
15. `orm.py` imports `domain.model`, never reverse; Django apps require `to_domain`/`update_from_domain` translation fns (no domain import of `django.db`).
16. Commands 1-handler, fail-loud; events N-handlers, fail-isolated + logged + retryable; new cross-aggregate work must arrive as event, not direct handler→handler call (or flagged as interim tech debt per epilogue Q&A).
17. Validation placed correctly: message-shape (`from_json`/schema/tolerant-reader) at edge/bus; `ensure.*`/ `ProductNotFound`/`SkipMessage` preconditions in service; stock/business rules in domain; overspecified field-format checks flagged.

### 7.4 Suggested automated guards (book doesn't provide these; skill would add)
- Import-linter contracts (`import-linter` `forbidden`/`layers`): `domain → adapters|entrypoints|config` forbidden; `service_layer → concretes` forbidden; `entrypoints → domain.model` discouraged (via commands/events only).
- Structural greps: `session.` outside `service_layer/unit_of_work.py|adapters/`; `send_mail|SMTP|redis.publish|requests.` outside `adapters/`+`bootstrap.py`; `Base|models.Model` subclass inside `domain/`; `mock.patch.*(Repository|UnitOfWork|MessageBus|Notifications)` in handler tests.
- Layout lint: required `domain/{model,events,commands}.py`, `service_layer/{handlers,messagebus,unit_of_work}.py`, `adapters/repository.py`, `bootstrap.py`, `views.py` (if reads exist), `tests/{unit,integration,e2e}/` split.
- Pyramid report: counts + "E2E duplicates handler path?" heuristic; missing unhappy-path test per command.

---

## 8. Gaps / cautions for skill design (from book itself)

- Book repeats: patterns pay off only past CRUD complexity; skill must not demand aggregates/bus/CQRS for simple apps ("just use Django"). Sources: Ch 2/7 trade-offs, App. D, Epilogue Q&A ("Do I need CQRS/microservices? No").
- No production-hardening in sample code: Redis pub/sub unreliable, no idempotency, no outbox, no schema versioning, bus `self.queue` not thread-safe, `time.sleep` concurrency repro is illustrative. Skill must require these before prod claims. Source: Epilogue `#footguns` https://www.cosmicpython.com/book/epilogue_1_how_to_get_there_from_here.html.
- Migration path is incremental (service layer → push logic to model / I/O to handlers → IDs over refs → SQL view builders → events → strangler/event-interception walking skeleton), not big-bang. Skill should support partial adoption + interim handler→handler calls with debt tags. Source: Epilogue + David Seddon "small steps" case study.
- ABCs are didactic; Pythonic enforcement may be duck-type/`Protocol` + review, not strict inheritance. Don't over-require ABC boilerplate. Sources: Ch 2, Ch 3, Ch 8 exercise.
- Each chapter's trade-off table should be preserved in skill guidance so reviewers can justify *not* applying a pattern.

---

## 9. Per-chapter trade-off tables (pointer)

- Ch 2 Repository: https://www.cosmicpython.com/book/chapter_02_repository.html (`#chapter_02_repository_tradeoffs`)
- Ch 4 Service layer: https://www.cosmicpython.com/book/chapter_04_service_layer.html (`#chapter_04_service_layer_tradeoffs`)
- Ch 6 UoW: https://www.cosmicpython.com/book/chapter_06_uow.html (`#chapter_06_uow_tradeoffs`)
- Ch 7 Aggregates: https://www.cosmicpython.com/book/chapter_07_aggregate.html (`#chapter_07_aggregate_tradoffs`)
- Ch 8 Domain events: https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html (`#chapter_08_events_and_message_bus_tradeoffs`)
- Ch 9 Whole-app bus: https://www.cosmicpython.com/book/chapter_09_all_messagebus.html (`#chapter_09_all_messagebus_tradeoffs`)
- Ch 10 Commands vs events: https://www.cosmicpython.com/book/chapter_10_commands.html (`#chapter_10_commands_and_events_tradeoffs`)
- Ch 11 External events: https://www.cosmicpython.com/book/chapter_11_external_events.html (`#chapter_11_external_events_tradeoffs`)
- Ch 12 View options: https://www.cosmicpython.com/book/chapter_12_cqrs.html (`#view_model_tradeoffs`)
- Canonical component table: https://www.cosmicpython.com/book/appendix_ds1_table.html

---

## 10. Source list (primary only)

- https://www.cosmicpython.com/ (landing + buy/free links)
- https://www.cosmicpython.com/book/preface.html
- https://www.cosmicpython.com/book/introduction.html
- https://www.cosmicpython.com/book/chapter_01_domain_model.html
- https://www.cosmicpython.com/book/chapter_02_repository.html
- https://www.cosmicpython.com/book/chapter_03_abstractions.html
- https://www.cosmicpython.com/book/chapter_04_service_layer.html
- https://www.cosmicpython.com/book/chapter_05_high_gear_low_gear.html
- https://www.cosmicpython.com/book/chapter_06_uow.html
- https://www.cosmicpython.com/book/chapter_07_aggregate.html
- https://www.cosmicpython.com/book/chapter_08_events_and_message_bus.html
- https://www.cosmicpython.com/book/chapter_09_all_messagebus.html
- https://www.cosmicpython.com/book/chapter_10_commands.html
- https://www.cosmicpython.com/book/chapter_11_external_events.html
- https://www.cosmicpython.com/book/chapter_12_cqrs.html
- https://www.cosmicpython.com/book/chapter_13_dependency_injection.html
- https://www.cosmicpython.com/book/epilogue_1_how_to_get_there_from_here.html
- https://www.cosmicpython.com/book/appendix_ds1_table.html
- https://www.cosmicpython.com/book/appendix_project_structure.html
- https://www.cosmicpython.com/book/appendix_csvs.html
- https://www.cosmicpython.com/book/appendix_django.html
- https://www.cosmicpython.com/book/appendix_validation.html
- https://github.com/cosmicpython/code (per-chapter branches cited in each chapter's tip box)
