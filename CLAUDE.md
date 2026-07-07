# E-commerce Customer Intelligence System (ShopSphere)

Synthetic-data e-commerce analytics pipeline: Python generators → MySQL medallion
(bronze → silver → gold) → EDA/Power BI → LinkedIn content. **Production quality,
never "MVP".** Victor does not read the code; orchestrator review is the only gate.

## HARD RULES
- Determinism: all generators seeded via `python/config/settings.py`. Same seed ⇒
  byte-identical CSVs. Never introduce unseeded randomness.
- Config/secrets only through `settings.py` + `.env`. No credentials in code or logs.
  Fail fast on missing secrets (already enforced — keep it).
- Destructive SQL only through allowlisted helpers (`python/utils/db_io.py`).
  Never raw `TRUNCATE`/`DELETE` against live MySQL from an ad-hoc shell.
- Bronze DDL and shipped migrations are append-only. Bronze data is immutable raw;
  cleaning happens bronze → silver, never in place.
- Errors surfaced, not swallowed. No `TODO` standing in for logic.
- No new dependencies without asking. Stay inside the task's listed files.
- If a brief's premise is wrong (bug elsewhere, already fixed), STOP and report.

## GATES (run before claiming done; numbers go in the report)
- Tests: `./.venv/Scripts/python.exe -m pytest -q` — count never drops.
- Calibration hard gate: `./.venv/Scripts/python.exe python/01_generate/calibration_check.py`
  — 8/8 PASS required after any generator change.
- Cleaning batches: data-quality report graded against `docs/dirty_data_manifest.md`
  (every injected defect class must be caught or explicitly waived).
- Pure refactors: output CSVs / query results **byte-identical** before vs after.
- Gates run against frozen data (`data/raw/` from a fixed seed), refreshed
  deliberately between batches, never during one.

## ORCHESTRATION
- Orchestrator plans, reviews, merges. Implementation is delegated; exception:
  trivial one-file edits needing no verification beyond the gates.
- Backend/schema work gets a short written plan before implementation.
- Review pipeline: every significant diff (>400 lines, or touching money-like
  logic, DB writes, or the calibration engine) gets an adversarial second review
  attacking the diff's named claims — see `docs/review-rigor-policy.md`.
- Never accept self-reported success: re-run tests + calibration personally
  before merge, in one batched shell call, output filtered (`tail`/`grep`).
- Shell discipline: batch related commands, filter every output, one task per
  context window. The binding budget is the rolling Claude session cap.

## CONTEXT (lazy-load ON DEMAND only — never "just to be safe")
- Board: `tasks/todo.md` (plan + progress + review). Lessons: `tasks/lessons.md`.
- Data model: `docs/01_DATA_MODEL_AND_DICTIONARY.md`. Setup: `docs/SETUP.md`.
- Defect ground truth: `docs/dirty_data_manifest.md`. Calibration: `docs/calibration_report.md`.
- Update `tasks/todo.md` review section at every significant session end, written
  for a cold-started different model, with a GOTCHAS list.

## WORKING WITH VICTOR
- Report numbers, not adjectives. Volunteer what went wrong and what you skipped.
- Surface: anything user/public-facing, money/accounts/credentials, irreversibles.
  Frame as options + recommendation, not essays.
- Only work on explicitly assigned tasks; don't wander the board.
