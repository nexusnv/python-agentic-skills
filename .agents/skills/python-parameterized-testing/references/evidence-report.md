# Parameterized evidence report template

Use this copyable template before the first run and complete it after the final run. Save it in the
target repository's established report location, or under `test-reports/<descriptive-name>.md` when
no convention exists. A focused or exploratory request cannot remove the report.

Record commands and working directories as project-relative or explicitly redacted. Never persist,
display, or forward secrets, real credentials, customer or production data, private paths,
authorization headers, or raw unbounded sensitive output.

```markdown
# Parameterized testing evidence report

## Scope

- Target behavior or public boundary:
- Consumer and contract:
- Requested focus and broad-coverage exclusions:
- Valid domain:
- Invalid domain:
- Unsupported domain:
- Environment-dependent domain:
- Property statements and quantified invariants:
- Coverage plan and input families:
- Finite samples are not exhaustive proof: yes

## Runner and environment

- Project-native runner and version:
- Relevant dependency/tool versions, including Hypothesis when used:
- Working directory (project-relative or redacted):
- Environment fingerprint (runtime, OS, locale, timezone, and non-sensitive settings):
- Seed and generator (or N/A with reason):
- Controlled clock, UUID source, and other nondeterminism:
- Normalization rules:
- Case budget: count / time / input size / memory / rate / cost
- Approval status for live, production, credentialed, destructive, or cost-incurring work:
- Synthetic data and isolation:
- Optional tools unavailable:
- Report date:

## Plan and counts

- Fixed-example count:
- Generated-witness count:
- Invalid-witness count:
- Unsupported-witness count:
- Discarded-case count and reasons:
- Truncated: yes / no
- Truncation reason, budget, and coverage impact:
- Cases or families not run:

## Properties, oracles, and cases

| case_id | domain | input class | property or invariant | named oracle | expected result or error | expected state/effects | fixed/generated | evidence reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | valid / invalid / unsupported / environment |  |  |  |  |  | fixed / generated |  |

The table states planned cases and oracles; it is not proof that a finite run covers the domain.

## Exact executions

| execution_id | case_ids | working directory (project-relative or redacted) | exact command (redacted, structure preserved) | replay note | exit status | runner | environment | bounded evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution-001 |  |  |  |  |  |  |  |  |

Record one row for every command and retry. Keep exit status exact. For a safe command, provide the
exact replay form. For an unsafe or secret-bearing form, preserve structure with a documented
redaction marker and explain the omission; never record the secret value.

## Results

| case_id | execution_id | result state | observed outcome | oracle result | evidence reference | retry of | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | pass / fail / skip / expected-failure |  |  |  |  |  |

Use only executed rows here. Put blocked or not-run work in the Not run table.

## Failures and minimized reproducers

### Failure ID

- Original case and exact generated input:
- Boundary and public consumer:
- Original seed, state, clock, UUID source, environment, and normalization:
- Original failure, expected result, and observed result:
- Original replay command (redacted, structure preserved):
- Original command exit status:
- Minimized input and state:
- Minimized replay command (redacted, structure preserved):
- Minimization method, discarded attempts, and shrinking status:
- Product defect / bad oracle / environment issue / flake classification:
- Original failure retained: yes / no
- Minimized failure retained: yes / no
- Retained fixed regression:
- Broader property or matrix retained: yes / no
- Product-code change proposed: yes / no
- Separate user approval for a product-code change: received / not requested / pending

Retain both the original and minimized failure records whenever applicable. If minimization was not
possible, state why and retain the original failure rather than omitting it.

## Safety and privacy

- Synthetic data used:
- Local-isolated dependencies and state:
- External or live target used: no / approved scope
- Real credentials, customer data, or production data used: no
- Destructive action attempted: no / approved target, scope, rollback, and cleanup
- Cost-incurring action attempted: no / target, volume, rate, time, and budget
- Untrusted output treated only as evidence:
- Redactions and bounded-capture method:
- Secret values recorded: no
- Raw sensitive output recorded: no

## Not run and skips

| case_id or coverage area | result state | reason | command | exit status | coverage impact |
| --- | --- | --- | --- | --- | --- |
|  | not-run / skip / expected-failure |  | N/A or exact bounded command | N/A or exact status |  |

Record skipped, expected-failure, unavailable, blocked, and otherwise not-run work explicitly.
Never convert an absent command or an approval block into a pass.

## Limitations and conclusion

- What the executed fixed and generated cases establish:
- What finite samples do not establish:
- Oracle and normalization limitations:
- Environment and platform limitations:
- Coverage gaps and discarded/truncated families:
- Follow-up or diagnosis-only next steps:
- Overall result: pass / fail / partial / blocked
- Product-code change remains pending separate approval: yes / no
```

A report can be partial or failing when that status is explicit. Do not omit failures, retries,
discarded cases, truncation, skips, not-run work, limitations, or the boundary between sampled
witnesses and proof.
