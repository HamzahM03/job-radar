# job-radar Architecture

## Goal

A personal tool that monitors NYC tech job postings from the Greenhouse,
Lever, and Ashby public APIs, filters them against a resume and preferences,
and notifies about postings worth applying to. It never auto-applies — the
final decision and submission are always manual.

## Constraints

- Runs on one personal machine, for one user.
- Python, SQLite for storage and deduplication.
- Deterministic rule-based filters (title, location, years of experience)
  run before any LLM call, to keep API costs near zero.
- An LLM is only used to judge ambiguous cases against the resume.
- Notifications via Discord webhook (not native OS notifications).
- No automated job applications, ever, under any circumstance.
- Triggered manually (`python main.py`) for now. Windows Task Scheduler will
  call the same script unchanged once the pipeline is proven — no scheduling
  code is built yet.
- Optimized for understanding every decision, not for finishing fast — avoid
  speculative abstractions and dependencies added without discussion.

## Components

- `fetchers/{greenhouse,lever,ashby}.py` — one module per ATS, each exposing
  a function that takes a board token and returns a list of job postings in
  a common shape (id, title, location, url, description, raw source data).
- `db.py` — SQLite access. One `jobs` table, unique on `(source,
  external_id)`, used both for deduplication and for tracking each job's
  pipeline state (new / rejected / ambiguous / accepted / notified / error).
- `filters.py` — deterministic rule engine. Applies title keyword rules,
  location rules, and years-of-experience rules from `preferences.yaml` to
  a job, returning one of: reject, accept, ambiguous.
- `llm_judge.py` — calls the OpenAI API for ambiguous jobs only, given the
  resume text (`resume.md`) and the job description, returning a verdict
  plus short reasoning that gets stored alongside the job.
- `notifier.py` — sends a Discord webhook message for each accepted job.
- `main.py` — orchestrates the pipeline: for each company in
  `companies.yaml`, fetch postings, check the DB for dedup, run
  deterministic filters, run the LLM judge on ambiguous jobs, notify on
  accepted jobs, and write each job's final state to the DB immediately.
- `companies.yaml` — hand-maintained list of companies to monitor: name,
  ATS type, board token.
- `preferences.yaml` — deterministic filter rules: title include/exclude
  keywords, location rules, min/max years of experience.
- `resume.md` — plain-text/markdown resume, read directly into LLM prompts.

## Data flow

```
companies.yaml
      |
      v
for each company -> fetchers/{ats}.py -> raw postings
      |
      v
db.py: has this (source, external_id) been seen? --yes--> skip
      | no
      v
filters.py (preferences.yaml) --reject--> write "rejected" to db, stop
      | ambiguous                | accept
      v                          |
llm_judge.py (resume.md)         |
      | reject        | accept   |
      v                v---------+
write "rejected"       notifier.py --> Discord webhook
to db, stop                   |
                               v
                     write "accepted"/"notified" to db
```

Each job's outcome is written to the database as soon as it's known, not
batched at the end of the run.

## Key decisions and reasoning

1. **Dedup by `(source, external_id)`, not by title/company text.** The
   ATS's own posting ID is stable and unambiguous; matching on text would
   risk false positives (two different postings with the same title) or
   false negatives (the same posting reworded).
2. **Filters produce three outcomes: reject / accept / ambiguous**, not just
   pass/fail. "Ambiguous" means the deterministic rules can't confidently
   decide — for example, years of experience isn't stated in the posting, or
   the title is a borderline match. Only ambiguous jobs reach the LLM, which
   is what keeps LLM API calls near zero.
3. **The LLM is called per-ambiguous-job, not batched or cached beyond the
   database.** Volume is expected to be small enough (a handful of ambiguous
   postings per run, at most) that a more elaborate batching or caching
   scheme isn't justified yet. The verdict and reasoning are stored in the
   database so past decisions stay inspectable.
4. **One Discord message per accepted job, not a digest.** Expected
   post-filter volume is low; a digest would add complexity (batching
   window, formatting a multi-job message) that doesn't pay for itself yet.
5. **Config lives in YAML files, not a database or admin UI.** There's one
   user hand-editing these occasionally — a plain-text, git-diffable file is
   simpler to read and change than anything with a schema migration story.
6. **Resume is plain text/markdown, read directly into the prompt.** No
   PDF-parsing dependency, no embeddings or vector search — the whole resume
   is small enough to include directly, and retrieval would be solving a
   scale problem this project doesn't have.
7. **No scheduling code.** `main.py` is a plain script run by hand. Task
   Scheduler will invoke it later without any changes to the script itself,
   so building scheduling logic now would be speculative.
8. **Sequential fetching, no concurrency.** With a personal watchlist of
   tens of companies, sequential HTTP calls take at most a couple of
   minutes; async/concurrent fetching would add complexity with no
   observable benefit at this scale.
9. **Per-job DB writes instead of staged tables.** Writing each job's
   outcome to the database as soon as it's decided (rather than holding
   results in memory until the end of the run, or introducing separate
   staging tables per pipeline phase) means the script is safe to interrupt
   and rerun: dedup and per-job status prevent duplicate notifications or
   lost jobs, without the added bookkeeping of a fully staged pipeline.

## Reconsider this when...

- The company list grows large enough (~100+ boards) that a sequential
  fetch run takes more than a minute or two — consider concurrent fetching.
- Fetch and judge/notify need to run on different cadences (e.g. fetch
  hourly, only notify during waking hours) — this is when splitting the
  pipeline into independently-runnable stages with their own DB tables
  starts to earn its complexity.
- Discord notification volume becomes noisy — switch from per-job messages
  to a batched digest.
- LLM-judged (ambiguous) volume grows large enough to matter for cost —
  tighten the deterministic rules to shrink the ambiguous bucket, or add
  caching beyond what the database already provides.
- Another consumer of the job data appears (e.g. a dashboard) — extract a
  proper data-access layer instead of ad hoc SQL in each module.
- The manual pipeline is proven reliable — wire `main.py` into Windows Task
  Scheduler, unchanged.
