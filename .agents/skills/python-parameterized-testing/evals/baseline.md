# Parameterized skill qualitative baseline notes

- **Date:** 2026-09-24
- **Run type:** Four read-only subagent sessions
- **Evidence class:** Qualitative observations derived from session summaries, not raw transcripts or a controlled benchmark

These four read-only subagent sessions were run on 2026-09-24 before the parameterized skill was added.
Raw transcripts were not committed. The session IDs below identify those read-only runs. Each
observation is an authored summary derived from the recorded session summary, not a raw transcript,
an independently reproducible result, or a controlled benchmark. The repeatable evaluation fixtures
remain in `cases.yaml`.

## 1. Random encoder and proof classification

**Read-only subagent session:** `ses_f2df871b6ffelLlsMDUuXBtiz6`

**Condensed observation**

> correctly distinguished finite deterministic samples from proof, but accepted the user’s no-report request;

**Design implication**

Preserve the accurate distinction between finite deterministic samples and proof. Make the evidence
report mandatory rather than allowing a no-report request to remove the record of the oracle, seed,
coverage limits, and what was not run.

## 2. Invalid-domain handling and evidence

**Read-only subagent session:** `ses_f2df871b4ffeeHGpYqdKWO5b6U`

**Condensed observation**

> used early returns and omitted seed/discarded/not-run evidence, the concrete gap;

**Design implication**

Require explicit valid, invalid, and unsupported domains; prohibit early returns and silent filtering
that hide hard cases. Require seed, discarded-case count, and not-run evidence whenever generated
cases are planned or run, with the concrete omission called out as a failure mode to prevent.

## 3. Live fuzz pressure, budgets, and approval

**Read-only subagent session:** `ses_f2df871b3ffeBTcjEKpUJGDWIT`

**Condensed observation**

> strong safety/budget/approval behavior, preserve it;

**Design implication**

Preserve explicit approval gates for live services, production data, destructive operations, and
cost-incurring calls. Keep generation bounded by an explicit budget and report truncation or
stratification; a safety refusal must not be replaced by an unreviewed live or unbounded run.

## 4. Flaky replay and retained failures

**Read-only subagent session:** `ses_f2df871b1ffeZIC24O245hf9oA`

**Condensed observation**

> strong replay/state diagnosis, but make minimized input and original failure retention mandatory in the skill;

**Design implication**

Preserve exact replay, seed/environment recording, and state diagnosis. Make the minimized input
and the original failing case mandatory retained evidence, not optional follow-up, and clearly label
shrinking or minimization status.
