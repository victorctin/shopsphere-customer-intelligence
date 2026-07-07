# Review Rigor Policy

Adapted from the Fable-5 orchestration handover (`~/Downloads/FABLE-5-INTELLIGENCE.md`, §II).
Purpose: no diff merges on the author's word alone; significant diffs get an
adversarial second review by a reviewer that did not author them.

## When a second review is MANDATORY
- Diff > 400 lines, or high blast radius regardless of size.
- Anything touching: DB writes/DDL, the calibration engine, revenue/CAC math,
  the dirty-data injector or its manifest, credentials/config handling.

## Reviewer lanes (in preference order)
1. **Codex GPT-5.5 xhigh via `codex exec`** — NOT currently installed on this
   machine (verified 2026-07-07). If Victor installs it, it becomes the default
   reviewer lane (bills to OpenAI, not the Claude session cap):
   `codex exec -c model_reasoning_effort="xhigh" "<review prompt>"`
2. **Fresh Claude agent, zero shared context** — spawn a reviewer agent whose
   prompt contains only the diff (or branch ref) and the review template below.
   Never the agent that authored the batch; never the orchestrator's own
   context pasted in.
3. Orchestrator line-level sweep of dangerous categories (always, in addition):
   DB writes, money math, seeded randomness, error handling.

## The adversarial review prompt template
```
You are doing an adversarial correctness/data-integrity review of this diff.
Do NOT modify files.

The diff CLAIMS the following. Attack each claim — find inputs, orderings, and
data shapes under which it is false:
1. <claim from the author's completion report, verbatim>
2. <...>

Also hunt beyond the claims: silent row drops, joins that fan out or lose rows,
NULL/duplicate handling gaps, timezone/date-boundary bugs, unseeded randomness,
constraint violations bronze→silver, places where a comment or doc promises a
mechanism (dedupe, idempotency, FK cascade, allowlist) the code does not
actually implement, and destructive SQL outside the allowlisted helpers.

Output: numbered findings with severity (critical/major/minor), file:line, the
concrete failing scenario, and the minimal fix. No praise. No style nits unless
they hide a bug.
```

## Remediation discipline
- Findings go back to the author as an enumerated list. Every remediated finding
  ships WITH a test that would have caught it. Disputes come to the orchestrator.
- Major/structural remediation ⇒ loop the new diff back through review.
- Default triage stance: a finding is real until the author refutes it concretely.

## Independent verification (orchestrator, every merge — one batched call)
```
./.venv/Scripts/python.exe -m pytest -q --tb=no 2>&1 | tail -3
./.venv/Scripts/python.exe python/01_generate/calibration_check.py 2>&1 | tail -10
```
- Test count matches the author's claim and never drops.
- Calibration 8/8 PASS after any generator-adjacent change.
- Cleaning diffs: quality report catches every class in `docs/dirty_data_manifest.md`.
- For every assumed invariant in a design, demand the file:line where it is
  enforced (the phantom-lock rule). "The doc says so" is not enforcement.
