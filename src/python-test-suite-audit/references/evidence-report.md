# Audit scorecard report template

Use this copyable template before the first run and complete it after the final run. Save it in the
target repository's established report location, or under `test-reports/<descriptive-name>.md` when
no convention exists. A focused or quick request cannot remove the report.

Record commands and working directories as project-relative or explicitly redacted. **Unconditionally
refuse real secrets, live credentials, customer data, and production data.** Approval may permit
only a narrowly scoped, non-sensitive live call, destructive operation, or cost-incurring action;
approval never authorizes secret or data access. Never persist, display, or forward those values,
private paths, authorization headers, or raw unbounded sensitive output. Static findings are
advisory until confirmed by execution.

```markdown
# Test suite audit scorecard

## Scope

- Audit target or public boundary:
- Consumer and contract:
- Audit profile: quick / deep
- Requested focus and broad-coverage exclusions:
- Property statements and quantified invariants:
- Coverage areas/plan:
- Dimensions assessed: executability, assertion rigor, coupling, error depth, isolation, maintainability
- Static findings are advisory until confirmed by execution: yes

## Runner and environment

- Project-native runner and version:
- Relevant dependency/tool versions, including mutation tool when used:
- Working directory (project-relative or redacted):
- Environment fingerprint (runtime, OS, locale, timezone, and non-sensitive settings):
- Seed and generator (or N/A with reason):
- Controlled clock, UUID source, and other nondeterminism:
- Normalization rules:
- Audit budget: files / findings / time
- Approval status for permitted non-sensitive live, destructive, or cost-incurring work:
- Synthetic data and isolation:
- Optional tools unavailable:
- Report date:

## Findings

| finding_id | severity | dimension | location | evidence | risk_if_ignored | proposed_remediation | confirmed |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  | Critical / Major / Minor |  |  |  |  |  | yes / no |

The Findings table states one row per advisory or confirmed issue. Cap unconfirmed static
patterns at Minor with confirmed set to no.

## Exact executions

| execution_id | case_ids | working directory (project-relative or redacted) | exact command (redacted, structure preserved) | replay note | exit status | runner | environment | bounded evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution-001 |  |  |  |  |  |  |  |  |

Record one row for every command and retry. Keep exit status exact. For a safe command, provide the
exact replay form. For an unsafe or secret-bearing form, preserve structure with a documented
redaction marker and explain the omission; never record the secret value.

## Results

| case_id | execution_id | result_state | observed outcome | oracle result | evidence reference | retry of | notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | pass / fail / skip / expected-failure |  |  |  |  |  |

Use only executed rows here. Put blocked or not-run work in the Not run and skips table.

## Not run and skips

| case_id or coverage area | result_state | reason | command | exit status | coverage impact |
| --- | --- | --- | --- | --- | --- |
|  | not-run / skip / expected-failure |  | N/A or exact bounded command | N/A or exact status |  |

Record skipped, expected-failure, unavailable, blocked, and otherwise not-run work explicitly.
Never convert an absent command or an approval block into a pass.

## Limitations and conclusion

- What the audit establishes:
- What the audit does not establish:
- Oracle and normalization limitations:
- Environment and platform limitations:
- Coverage gaps and discarded/truncated families:
- Follow-up or diagnosis-only next steps:
- Overall result: pass / fail / partial / blocked
- Product-code or test-code change remains pending separate approval: yes / no
```

A report can be partial or failing when that status is explicit. Do not omit failures, retries,
discarded cases, truncation, skips, not-run work, limitations, or the boundary between static
patterns and confirmed findings.
