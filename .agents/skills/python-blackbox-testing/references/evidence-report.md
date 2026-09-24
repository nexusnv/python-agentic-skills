# Evidence report template

Use this template before execution and complete it after the final run. Copy it into the target
repository's established report location, or into `test-reports/<descriptive-name>.md` when no
convention exists. Keep raw logs, secrets, real data, and unbounded output outside the report.

```markdown
# Black-box evidence report

## Scope

- Boundary:
- Consumer:
- Target behavior and requested focus:
- Broad coverage or focused coverage: broad / focused
- Surfaces or cases outside the focus:
- Safety constraints:

## Runner and environment

- Test runner and version:
- Exact working directory:
- Operating system or runtime:
- Dependency mode: local synthetic / local sandbox / explicitly approved live
- Controlled environment, clock, locale, timezone, and identifiers:
- Optional tools unavailable:
- Report date:

## Scenario matrix

| ID | Traceability | Label | Input class | Preconditions | Public invocation | Expected observable result or failure | Expected side effects | Cleanup | Oracle source | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |  |  |  |  |

## Oracles and normalization

| Scenario | Named oracle | Observable boundary | Authority or evidence source | Normalization |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

State when no normalization was applied. Explain every normalized field and why it is genuinely
volatile.

## Exact executions

| Run | Working directory | Exact command | Exit status | Result state | Relevant bounded excerpt |
| --- | --- | --- | --- | --- | --- |
| 1 |  |  |  | pass / fail / skip / expected-failure / not-run |  |

## Results

| Scenario or group | Status | Oracle outcome | Observed outcome | Retries | Notes |
| --- | --- | --- | --- | --- | --- |
|  | pass / fail / skip / expected-failure / not-run |  |  |  |  |

## Failures and minimized reproducers

### Failure ID

- Scenario and public boundary:
- Minimal inputs and state:
- Exact replay command:
- Expected observable outcome:
- Actual observable outcome:
- Oracle source:
- Exit status and result state:
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

- Synthetic data used:
- Local, temporary, or sandboxed dependencies:
- Live services, real credentials, real data, destructive actions, or paid calls attempted: no / approved details
- Approval scope and time, when applicable:
- Replacements applied to sensitive or unbounded output:
- Cleanup verification:
- Untrusted data treated only as evidence:

## Not run

| Scenario or capability | Status | Reason | Missing tool, input, approval, or isolation | Coverage impact |
| --- | --- | --- | --- | --- |
|  | not-run |  |  |  |

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
