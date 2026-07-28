# job-scout

[![Tests](https://github.com/FloDudu/job-scout/actions/workflows/test.yml/badge.svg)](https://github.com/FloDudu/job-scout/actions/workflows/test.yml)

Automated triage pipeline for job offers: turns a folder of scraped LinkedIn
postings into scored, reasoned reports — interest score, priority fit,
points to watch, near-duplicate detection, and CV tailoring notes — without
re-reading every offer by hand.

This is a **RAG + classification pipeline**, not an autonomous agent: every
run follows the same fixed steps (parse → enrich → analyze → store), there
is no dynamic planning or tool selection by the model.

## How it works

```
Downloads/ODE_*.txt
        │
        ▼
   parse_offer          extract TITRE / ENTREPRISE / LOCALISATION / URL /
        │                 DESCRIPTION
        │
        ▼
   enrich_offer         Claude Haiku 4.5 — location, work mode, salary
        │                (structured output; the raw LOCALISATION field
        │                 from the source file is unreliable, see below)
        ▼
   dedup check          two-tier: normalized-text hash first (free), then
        │                 VoyageAI embedding + cosine similarity against
        │                 stored offers only if the hash tier found nothing
        ▼
   analyze_offer        Claude Sonnet 5 — score, priority, reasoning,
        │                points to watch, duplicate flag, CV tailoring
        │                notes (structured output, candidate profile
        │                cached as a system prompt). A duplicate is always
        │                flagged in the report, never auto-skipped.
        ▼
   save_offer            persist to SQLite
        │
        ▼
   move_to_processed/    keep the source folder clean; a failed offer goes
   move_to_errors         to ODE_errors/ instead of blocking the batch
```

Each offer is scored against two priorities set in the candidate's profile
(e.g. "target role" vs. "acceptable fallback") rather than a single
relevance number — the report always states which one an offer matches.
Priority-2 (fallback) offers are capped at 8/10 so they can never outrank
a priority-1 match on raw score. A derived `action` (Postule / Candidature
légère / Passe, from the score) is computed on the fly wherever an offer
is displayed — never stored, so it stays correct if the thresholds change.

## Stack

- Python 3.10+, [uv](https://docs.astral.sh/uv/) for dependency management
- [Anthropic API](https://platform.claude.com) — Claude Haiku 4.5 (extraction) /
  Claude Sonnet 5 (judgment), both via structured (Pydantic) output
- [VoyageAI](https://www.voyageai.com/) (`voyage-3`) — embeddings for the
  second-tier duplicate check
- SQLite for storage
- pytest, with the Anthropic client mocked for the modules that call it
  (no live API calls in the test suite)

## Setup

```bash
uv sync
cp .env.example .env   # fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY
```

The engine (`src/`) is generic; personal data lives in `config/` and is
**never committed**:

- `config/profile.md` — candidate profile: experience, dual priority,
  non-negotiable constraints (location, salary floor, legal status), CV
  variants
- `config/cvs/` — the actual CV files referenced by `profile.md`

Neither exists in a fresh clone — write your own before running the tool.
[`config/profile.example.md`](config/profile.example.md) (fictional data,
versioned) shows the expected shape — copy it to `config/profile.md` and
replace the content with your own.

## Usage

```bash
uv run job-scout
```

Scans the configured source directory (defaults to `~/Downloads`, override
with `JOB_SCOUT_SOURCE_DIR`) for `ODE_*.txt` files captured by the
[bookmarklet](tools/bookmarklet.js), and processes each one:

```
[3/10, priority 2, Passe] Backend Engineer - Acme Corp
[8/10, priority 1, Postule] ML Engineer - Widget Inc

Done: 2 processed, 0 errors.
```

Full reasoning, points to watch, and CV notes are stored per offer in
SQLite (`data/job_scout.db`), not printed to the console — view them with
`job-scout show`.

Update an offer's status once you've acted on it (the offer's `id` is its
row in the database):

```bash
uv run job-scout status 3 applied
```

Valid statuses: `new` (default), `applied`, `interview`, `rejected`,
`no_response`.

Export a quick-scan table (id, title, company, location, URL, work mode,
salary, priority, score, status, action) to CSV — opens directly in Excel:

```bash
uv run job-scout export                    # data/offers_export.csv
uv run job-scout export path/to/file.csv   # custom path
```

Generate a cover letter on demand (not part of the automatic batch run,
grounded in the candidate profile and the offer's already-stored analysis
report, so it reflects the same CV tailoring notes):

```bash
uv run job-scout letter 3 en   # or fr
```

List all offers sorted by score (highest first), with the derived
`action` — the fastest way to see what to act on next without opening a
CSV:

```bash
uv run job-scout list
```

Filter by capture date and/or to only the offers worth acting on (action
is Postule or Candidature légère, i.e. score >= 6) — e.g. to answer
"which offers from today should I apply to":

```bash
uv run job-scout list --date 2026-07-27 --actionable
```

Show the full stored report for an offer (score, priority, status,
location/work mode/salary, URL, and the full reasoning/points to
watch/CV notes):

```bash
uv run job-scout show 3
```

Export full reports (same content as `show`) for a set of offers to a
plain text file — same `--date`/`--actionable` filters as `list`, useful
as a single document to have on hand while actually applying:

```bash
uv run job-scout brief --date 2026-07-27 --actionable
# data/offers_brief.txt by default, or:
uv run job-scout brief --actionable path/to/file.txt
```

## Project layout

```
src/job_scout/
├── config.py       env/client setup (API key, timeouts, shared HTTP client)
├── ingestion.py     find/read/move offer files
├── parser.py        TITRE/ENTREPRISE/LOCALISATION/DESCRIPTION -> ParsedOffer
├── enrichment.py     location / work mode / salary extraction (Haiku)
├── dedup.py           two-tier duplicate detection (hash, then VoyageAI
│                        embeddings + cosine similarity)
├── profile.py        loads config/profile.md as a cached system prompt
├── prompt.py          builds the analysis prompt
├── analysis.py        the scoring call (Sonnet 5)
├── db.py / storage.py  SQLite schema and persistence
├── export.py           CSV export and full-report text export (brief)
├── letter.py            on-demand cover letter generation (Sonnet 5)
└── cli.py              ties it all together
tools/bookmarklet.js    LinkedIn capture script
tests/                  full module coverage - Anthropic client mocked for
                        analysis/enrichment/letter, no live calls
```

## Status

Actively built, ticket by ticket (tracked via GitHub Issues/Projects). The
full pipeline is functional end to end: ingestion, duplicate detection,
scoring, status tracking, CSV export, and on-demand cover letter
generation.
