# Boundaries and oracles

Use this reference to define what a consumer can observe, label the purpose of each scenario, and
name an oracle before running it.

## Public and private boundaries

A **public boundary** is an interface supported for a real consumer, including an installed Python
API, documented CLI command, HTTP/RPC operation, stable file format, database contract, published
event, or supported user workflow. A black-box case invokes that interface with synthetic or
approved inputs and asserts an observable result, state transition, error, or side effect.

A **private boundary** is an internal helper, module global, non-exported class, exact call sequence,
or implementation detail that a consumer cannot rely on. Do not assert private call order by
default. Private structure may be inspected only for diagnosis after an observable failure or when
the user explicitly requests a white-box test, and it must not replace an available public seam.

If no public seam exists:

1. Report the missing or inaccessible boundary.
2. Describe what a consumer can currently observe.
3. Propose the smallest public seam needed for a durable contract.
4. Mark private-only verification as lower-confidence and do not present it as black-box coverage.

## Lowest useful test pyramid level

Choose the lowest level that still represents the contract and its consumer:

1. Start with a direct public Python API when that is the supported interface.
2. Use a CLI subprocess when argument parsing, streams, exit status, or files are part of the
   contract.
3. Use HTTP/RPC when transport, serialization, status, headers, or protocol compatibility matter.
4. Use filesystem or database adapters when persistence, migration, file format, or transactional
   behavior is the risk.
5. Use event or message boundaries when ordering, delivery, idempotency, or schema compatibility
   matters.
6. Use UI automation only when user-observable workflow behavior is the actual contract.

Do not raise the test level merely to make coverage look broad. Raise it when the lower boundary
would miss behavior owned by the public interface.

## Scenario labels

- **Contract:** Assert behavior supported by documentation, a published schema, an approved
  specification, or a reviewed business rule. Keep the oracle source traceable.
- **Characterization:** Record current observable behavior that lacks enough authority to call it
  correct. Label the gap as an open question and avoid correctness claims.
- **Regression:** Preserve a previously supported outcome, a fixed defect reproducer, or a newly
  confirmed contract. Give the defect and public entry point clear traceability.
- **Suspicious current behavior:** Record an observed outcome that appears unsafe, contradictory,
  or inconsistent with adjacent public behavior without assuming the implementation is wrong or
  right. Escalate it for review.

A scenario can exercise more than one concern, but give it one primary label and record secondary
relationships explicitly.

## Oracle types

A named oracle must say **what is observed**, **where it is observed**, and **why that observation
is authoritative**. Prefer these types:

- **Exact observable outcome:** return value, exit status, stdout/stderr, response body, event,
  or emitted message.
- **Stable error:** documented type/code and safe message fragment, without volatile identifiers or
  sensitive values.
- **State transition:** explicit before/after state visible through a public read boundary.
- **No-side-effect invariant:** observable state remains unchanged after an invalid or failed case.
- **Contract matcher:** schema, protocol, type, or documented cross-field rule.
- **Differential model:** compare the public result with a reviewed independent model or invariant.
- **Reviewed golden result:** a bounded expected artifact reviewed against an authoritative source.

Do not use string equality on unstable objects. Normalize only fields proven volatile, such as a
clock timestamp, random identifier, temporary path, or unordered collection. Record each
normalization and apply it before comparison, not after a failure.

A captured current output can support characterization, debugging, or a reviewed golden result. It
is not by itself a correctness oracle.

## Consumer adapters

Name the consumer and the adapter through which it observes behavior. Examples include a library
consumer calling a public function, a shell consumer running an installed command, an HTTP client
sending a request, or another service consuming an event.

The adapter defines what counts as input, output, error, state, and side effect. Keep consumer-facing
serialization and normalization in the test or fixture boundary. Do not inspect internal state to
decide whether an observable result is correct.

## Scenario matrix

Create a matrix before implementation. Use one row per scenario execution, keep `scenario_id`
stable across retries, and assign a unique `execution_id` to each command run. Include:

| Field | Required content |
| --- | --- |
| `scenario_id` | Stable scenario identifier reused across retries. |
| `execution_id` | `pending` before execution; unique identifier for one executed command; use `N/A` for blocked/not-run and record retry lineage separately. |
| Traceability | Public interface, contract, defect, or open question. |
| Label | Contract, characterization, regression, or suspicious current behavior. |
| Input class | Valid, invalid, boundary, stateful, negative, or another explicit behavioral family. |
| Preconditions | Synthetic state, setup, environment mode, isolation, and authorization assumptions. |
| Invocation | Public boundary and concrete consumer action. |
| Properties/invariants | Named properties or `N/A — example-only — reason` for pure fixed-example behavior. |
| Coverage areas/plan | Input families, boundaries, state transitions, and exclusions planned for this scenario. |
| Expected result | Named observable success outcome and oracle source. |
| Expected failure / not-applicable reason | Stable rejection outcome, or `not applicable` with a reason. |
| Expected side effects | Observable state/files/events that must change or remain unchanged. |
| Cleanup | Teardown, affected-resource limit, and verification where side effects occur. |
| `environment_mode` | `local-isolated`, `local-unisolated`, `external-live`, `external-sandbox-verified`, or `external-sandbox-unverified`. |
| `isolation_scope_verification` | Exact verification method and result, including why `local-unisolated` applies when relevant. |
| `run_approval_status` | `not-required`, `approved`, or `blocked`. |
| `run_approval_scope` | Target/method/data/volume/rate/time limits and paid-call budget, or destructive target/maximum resources/rollback/cleanup/permission. |
| `credential_approval_status` | `not-required`, `approved`, or `blocked`; using any test credential is a separate gate. |
| `credential_approval_scope` | Target/service, least-privilege, synthetic/test-only constraint, expiry/rotation, and volume/rate/time limits; never the credential value. |
| Safety status | Default-safe local isolation; approved side effect; verified external sandbox; manual/not-run gate; or unconditional refusal. |
| `planned_result_state` | Planned result state before execution; actual outcomes belong in the result table. |

A broad default matrix should cover the relevant input families and state transitions without
creating an uncontrolled Cartesian product. A requested focus narrows the prioritized set; record
excluded surfaces as coverage gaps rather than implying full coverage.
