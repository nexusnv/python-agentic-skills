# Property-based evidence report template

Use this copyable template before the first run and complete it after the final run. Save it in the
target repository's established report location, or under `test-reports/<descriptive-name>.md` when
no convention exists. A focused or exploratory request cannot remove the report.

Record commands and working directories as project-relative or explicitly redacted. **Unconditionally
refuse real secrets, live credentials, customer data, and production data.** Approval may permit
only a narrowly scoped, non-sensitive live call, destructive operation, or cost-incurring action;
approval never authorizes secret or data access. Never persist, display, or forward those values,
private paths, authorization headers, or raw unbounded sensitive output.

```markdown
# Property-based testing evidence report

## Scope

- Target behavior or public boundary:
- Consumer and contract:
- Requested focus and broad-coverage exclusions:
- Valid domain:
- Invalid domain:
- Unsupported domain:
- Environment-dependent domain:
- Property statements and quantified invariants:
- Strategy sketches and Hypothesis settings:
- Coverage plan and input families:
- Finite samples are not exhaustive proof: yes

## Runner and environment

- Project-native runner and version:
- Relevant dependency/tool versions, including Hypothesis when used:
- Hypothesis version and settings (or N/A with reason):
- Working directory (project-relative or redacted):
- Environment fingerprint (runtime, OS, locale, timezone, and non-sensitive settings):
- Seed and generator (or N/A with reason):
- Unicode replay evidence (when applicable): `unicodedata.unidata_version` or explicitly fixed
  whitespace character set:
- Controlled clock, UUID source, and other nondeterminism:
- Normalization rules:
- Case budget: count / time / input size / memory / rate / cost
- Approval status for permitted non-sensitive live, destructive, or cost-incurring work:
- Synthetic data and isolation:
- Optional tools unavailable:
- Report date:

## Plan and counts

- Fixed-example count:
- Generated-witness count:
- Invalid-witness count:
- Unsupported-witness count:
- Discarded-case count and reasons:
- Assume-filtered count and reasons:
- Truncated: yes / no
- Truncated count:
- Truncation reason, budget, and coverage impact:
- Shrinking status:
- Cases or families not run:

## Properties, oracles, and cases

| case_id | domain | input class | property or invariant | named oracle | strategy | expected result or error | expected state/effects | fixed/generated | evidence reference |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | valid / invalid / unsupported / environment |  |  |  |  |  |  | fixed / generated |  |

The table states planned cases, strategies, and oracles; it is not proof that a finite run covers the domain.

## Exact executions

| execution_id | case_ids | working directory (project-relative or redacted) | exact command (redacted, structure preserved) | replay note | exit status | runner | environment | bounded evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution-001 |  |  |  |  |  |  |  |  |

Record one row for every command and retry. Keep exit status exact. For a safe command, provide the
exact replay form. For an unsafe or secret-bearing form, preserve structure with a documented
redaction marker and explain the omission; never record the secret value.

## Results

| case_id | execution_id | result state | observed outcome | oracle result | strategy | evidence reference | retry of | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | pass / fail / skip / expected-failure |  |  |  |  |  |  |

## Failures and minimized reproducers

- Original case and exact generated input:
- Replay command for the original failure:
- Shrunken input and shrinking method:
- Discarded reduction attempts:
- Product defect, bad oracle, environment issue, or flake:
- Retained fixed regression:
- Broader property or matrix retained: yes / no

## Retained regressions

- Regression test location:
- Minimized input preserved as a fixed case: yes / no

## Safety and privacy

- Synthetic data used:
- Isolated local dependencies: yes / no
- Approval status for live, destructive, or cost-incurring work:
- Approval never authorized secret or data access: yes / no
- Redaction applied to commands, paths, and output: yes / no

## Not run and skips

| case id or coverage area | result state | reason | command | exit status | coverage impact |
| --- | --- | --- | --- | --- | --- |
|  | not-run / skip / expected-failure |  | N/A or exact bounded command | N/A or exact status |  |

Record blocked, skipped, expected-failure, and not-run work explicitly; never convert it into a
pass. Stateful sequences deferred to a later version are recorded here with their reason.

## Limitations and conclusion

- What finite samples do not establish:
- Coverage gaps and discarded/truncated families:
- Assume-filtered families and their coverage impact:
- Stateful sequences deferred:
- What was not run and why:
```

The template above is the canonical report contract. Every section heading and
marked field is required structurally; empty coverage areas stay present with an
explicit reason rather than being deleted.
