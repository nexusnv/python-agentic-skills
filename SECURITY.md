# Security Policy

## Important warning

Installed skills are agent instructions, not inert documents. A skill can direct an agent to execute
commands, inspect files, call local services, or use browser and network drivers. During a run, the
agent may also process untrusted repository content, test fixtures, HTTP responses, browser pages, logs,
and generated values. Review a skill and its references before installing it, and pin the repository
commit or release ref you intend to use for reproducibility.

Use local, sandboxed, synthetic data by default. Do not install or run a skill with secrets, live
credentials, production data, customer data, or unbounded logging. Require explicit approval before
live external services, destructive operations, persistent state changes, or cost-incurring calls.

## Reporting a vulnerability

Do not put private data, credentials, customer information, or exploit details in a public issue.
Report suspected vulnerabilities privately through GitHub's vulnerability reporting form:

<https://github.com/nexusnv/python-agentic-skills/security/advisories/new>

No response time is guaranteed. Please include, using synthetic or redacted material where possible:

- the affected skill, file, and commit/ref;
- the vulnerability type, impact, and relevant agent or client versions;
- minimal reproduction steps and the expected safe behavior;
- the commands or inputs that trigger the issue;
- any relevant logs, outputs, or proof with secrets and personal data removed;
- a suggested mitigation or patch, if you have one.

A report is not a public issue until maintainers decide otherwise. Avoid sending untrusted payloads or
running the suspected workflow against a live system as part of an initial report.
