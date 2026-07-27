# job-scout

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

## Stack

- Python 3.10+, [uv](https://docs.astral.sh/uv/) for dependency management
- [Anthropic API](https://platform.claude.com) — Claude Haiku 4.5 (extraction) /
  Claude Sonnet 5 (judgment), both via structured (Pydantic) output
- [VoyageAI](https://www.voyageai.com/) (`voyage-3`) — embeddings for the
  second-tier duplicate check
- SQLite for storage
- pytest for the modules that don't require live API calls

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

## Usage

```bash
uv run job-scout
```

Scans the configured source directory (defaults to `~/Downloads`, override
with `JOB_SCOUT_SOURCE_DIR`) for `ODE_*.txt` files captured by the
[bookmarklet](tools/bookmarklet.js), and processes each one:

```
[3/10, priority 2] Backend Engineer - Acme Corp
[8/10, priority 1] ML Engineer - Widget Inc

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
salary, priority, score, status) to CSV — opens directly in Excel:

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

Show the full stored report for an offer (score, priority, status,
location/work mode/salary, URL, and the full reasoning/points to
watch/CV notes):

```bash
uv run job-scout show 3
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
├── export.py           CSV export
├── letter.py            on-demand cover letter generation (Sonnet 5)
└── cli.py              ties it all together
tools/bookmarklet.js    LinkedIn capture script
tests/                  parser, ingestion, prompt, storage, export, and dedup
                        modules
```

## Status

Actively built, ticket by ticket (tracked via GitHub Issues/Projects). The
full pipeline is functional end to end: ingestion, duplicate detection,
scoring, status tracking, CSV export, and on-demand cover letter
generation.
