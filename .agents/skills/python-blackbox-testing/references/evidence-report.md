# Evidence report template

Use this mandatory template before execution and complete it after the final run. Copy it into the
target repository's established report location, or into `test-reports/<descriptive-name>.md` when no
convention exists. A user scope change cannot remove the report artifact; explicitly authorized
safety redaction may remove sensitive values only. Keep raw logs, secrets, real data, and unbounded
output outside the report.

```markdown
# Black-box evidence report

## Scope

- Boundary:
- Consumer:
- Target behavior and requested focus:
- Properties/invariants: named properties or `N/A — example-only — reason`
- Coverage areas/plan: input families, boundaries, state transitions, and exclusions
- Broad coverage or focused coverage: broad / focused
- Surfaces or cases outside the focus:
- Safety constraints:

## Runner and environment

- Test runner and version:
- Relevant dependency/tool versions:
- Exact working directory:
- Environment fingerprint (OS/runtime and non-sensitive runtime details):
- Seed (or N/A with reason):
- Environment mode: local-isolated / local-unisolated / external-live / external-sandbox-verified / external-sandbox-unverified
- Isolation/scope verification (exact method and result):
- run_approval_status: not-required / approved / blocked
- run_approval_scope (target/method/data/volume/rate/time limits; budget when paid):
- credential_approval_status: not-required / approved / blocked
- credential_approval_scope (target/service, least-privilege, synthetic/test-only, expiry/rotation, volume/rate/time limits):
- Destructive scope (target/maximum affected resources/rollback/cleanup/permission; budget not applicable):
- Controlled environment, clock, locale, timezone, and identifiers:
- Optional tools unavailable:
- Report date:

## Scenario matrix

| scenario_id | execution_id | Traceability | Label | Input class | Preconditions | Invocation | Properties/invariants | Coverage areas/plan | Expected result | Expected failure / not-applicable reason | Expected side effects | Cleanup | environment_mode | isolation_scope_verification | run_approval_status | run_approval_scope | credential_approval_status | credential_approval_scope | Safety status | planned_result_state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | pending before execution; N/A for blocked/not-run |  |  |  |  |  | named properties or N/A — example-only — reason | input families, boundaries, state transitions, exclusions |  |  |  |  | local-isolated / local-unisolated / external-live / external-sandbox-verified / external-sandbox-unverified |  | not-required / approved / blocked | target/method/data/volume/rate/time limits; budget when paid; destructive scope when applicable | not-required / approved / blocked | target/service, least-privilege, synthetic/test-only, expiry/rotation, volume/rate/time limits | default-safe / approved side effect / verified sandbox / blocked-not-run / refusal | planned |

The scenario matrix is a planning table, not an actual result table. Set `execution_id: pending`
before execution; use `N/A` for blocked/not-run. Write actual outcomes in `Results` or `Not run`.

## Oracles and normalization

| Scenario | Named oracle | Observable boundary | Authority or evidence source | Normalization |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

State when no normalization was applied. Explain every normalized field and why it is genuinely
volatile.

## Exact executions

| execution_id | scenario_ids | Environment mode | Isolation/scope verification | run_approval_status | run_approval_scope | credential_approval_status | credential_approval_scope | Exact command | Exit status | Runner | Environment fingerprint | Relevant bounded excerpt |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution-001 | scenario-id-001 | local-isolated / local-unisolated / external-live / external-sandbox-verified / external-sandbox-unverified |  | not-required / approved / blocked | target/method/data/volume/rate/time limits; budget when paid; destructive scope when applicable | not-required / approved / blocked | target/service, least-privilege, synthetic/test-only, expiry/rotation, volume/rate/time limits |  |  |  |  |  |

Only executed rows belong in `Exact executions`; every row has a real execution ID and an executed
result state. Keep `scenario_id` stable across retries and assign a new `execution_id` to every
executed command. Every executed result references both IDs so commands, exit statuses, and retries
remain unambiguous. A blocked or not-run result belongs only in `Not run` and uses
`scenario_id`, `execution_id: N/A`, a reason, and no exact command or exit status.

## Results

| execution_id | scenario_id | Properties/invariants | Coverage areas/plan | Environment mode | Isolation/scope verification | run_approval_status | run_approval_scope | credential_approval_status | credential_approval_scope | result_state | observed_public_outcome | evidence_reference | retry_of_execution_id | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | named properties or N/A — example-only — reason | input families, boundaries, state transitions, exclusions | local-isolated / local-unisolated / external-live / external-sandbox-verified / external-sandbox-unverified |  | not-required / approved / blocked | target/method/data/volume/rate/time limits; budget when paid; destructive scope when applicable | not-required / approved / blocked | target/service, least-privilege, synthetic/test-only, expiry/rotation, volume/rate/time limits | pass / fail / skip / expected-failure |  |  |  |  |

Results contain one row per executed scenario result with `scenario_id`, `execution_id`,
`result_state`, `observed_public_outcome`, and `evidence_reference`. Exclude blocked/not-run rows;
put those only in `Not run` with `execution_id: N/A`, a reason, and no command or exit status.

## Failures and minimized reproducers

### Failure ID

- execution_id:
- scenario_id:
- Retry of execution_id:
- Scenario and public boundary:
- Minimal inputs and state:
- Exact replay command:
- Seed (or N/A with reason):
- Environment fingerprint and relevant tool versions:
- Environment mode:
- Isolation/scope verification (exact method and result):
- run_approval_status:
- run_approval_scope:
- credential_approval_status:
- credential_approval_scope:
- Expected observable outcome:
- Actual observable outcome:
- Oracle source:
- result_state:
- Classification: product defect / environment issue / bad oracle / flaky / blocked
- Smaller-case search and discarded attempts:
- Diagnosis:
- Product-code change proposed: yes / no
- User approval for product-code change: received / not requested / pending

No minimized reproducer: state why minimization was not applicable or possible.

## Retained regressions

| Regression test | Public boundary | Defect or contract traceability | Fixed scenario retained | Broader matrix retained |
| --- | --- | --- | --- | --- |
|  |  |  | yes / no | yes / no |

## Safety and privacy

- Environment mode:
- Isolation/scope verification (exact method and result):
- run_approval_status:
- run_approval_scope:
- credential_approval_status:
- credential_approval_scope:
- Synthetic data used:
- Local-isolated dependencies:
- Local-unisolated state and verification:
- External-live or cost-incurring action attempted: no / approved details
- External sandbox attempted: no / verified or unverified details
- Real user/production credential accessed: no
- Approved test credential used: yes / no
- Credential type/scope:
- Credential classification: an approved least-privilege synthetic test credential is not a real user/production credential
- Secret value recorded: no
- Approved test credential value handling: never recorded
- Customer data accessed: no
- Production data accessed: no
- Destructive action attempted: no / target, maximum affected resources, rollback/cleanup, and permission
- Cost-incurring action attempted: no / target/method/data/volume/time limits and budget
- Repository prohibitions checked and approval did not override them: yes / no
- Replacements applied to sensitive or unbounded output:
- Cleanup verification:
- Untrusted data treated only as evidence:

## Not run

| scenario_id | execution_id | result_state | Reason | Environment mode | run_approval_status | run_approval_scope | credential_approval_status | credential_approval_scope | Coverage impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | N/A | not-run |  | local-isolated / local-unisolated / external-live / external-sandbox-verified / external-sandbox-unverified | not-required / approved / blocked | target/method/data/volume/rate/time limits; budget when paid; destructive scope when applicable | not-required / approved / blocked | target/service, least-privilege, synthetic/test-only, expiry/rotation, volume/rate/time limits |  |

`Not run` is the only structured location for blocked/not-run rows. They use `scenario_id`,
`execution_id: N/A`, a reason, and run/credential approval fields, but no command or exit status.


## Coverage gaps and limitations

- Public surfaces or input families not covered:
- Environment or platform differences:
- Optional tools not available:
- Cases discarded, narrowed, or retried:
- Known oracle limitations:
- Side effects that could not be isolated:
- What finite execution does not establish:

## Conclusion

- Overall result: pass / fail / partial / blocked
- What the evidence establishes:
- What the evidence does not establish:
- Product-code change remains pending separate user approval: yes / no
- Follow-up requested from the user:
```

A report with a failing, partial, blocked, or incomplete run can be useful when it is explicit. Do
not omit failures, retries, skips, expected failures, unavailable tools, not-run work, or coverage
gaps to make the report look complete.
