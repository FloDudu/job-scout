# Candidate profile

Copy this file to `config/profile.md` (gitignored, never committed) and
replace everything below with your own information. This file is loaded
as-is into the system prompt for every offer analysis (see
`src/job_scout/profile.py` and `src/job_scout/prompt.py`) - free-form
Markdown, no fixed schema, but the analysis prompt assumes the sections
below exist in some form.

## About me

Jane Doe, 6 years of professional software engineering experience,
based in Toronto, ON. Currently employed, open to new opportunities,
available with 4 weeks' notice.

## Priority 1 - target track: Machine Learning Engineer

Main career goal. No professional ML role yet - evidenced instead by:
- Coursera "Machine Learning Specialization" (2025)
- Personal project: a RAG-based documentation search tool (FastAPI,
  pgvector, OpenAI embeddings)
- Personal project: a fine-tuning experiment on a small classification
  task (PyTorch, HuggingFace)

## Priority 2 - fallback track: Backend Software Engineer

General backend engineering, financial fallback if priority-1 offers
are too scarce. 6 years across two companies - REST APIs, PostgreSQL,
Docker, CI/CD (GitHub Actions), Python and Go.

## Non-negotiable constraints

- Location: open to hybrid or fully remote (Toronto-based employers or
  remote-first companies only - no relocation)
- Salary floor: 90,000 CAD/year gross, non-negotiable
- Legal status: Canadian citizen, no sponsorship needed
- Languages: English (native), French (basic)
- Blacklist: none

## Skills

**Proficient:** Python, PostgreSQL, Docker, REST API design, pytest
**Intermediate:** Go, Kubernetes, PyTorch, LangChain

## CV variants

- `config/cvs/cv_ml_en.pdf` - title "Software Engineer | Machine Learning",
  use for priority 1 offers
- `config/cvs/cv_backend_en.pdf` - title "Backend Software Engineer",
  use for priority 2 offers

Both CVs cover the same underlying experience - only the title and
summary framing differ. `AnalysisResult.cv_notes` (see
`src/job_scout/analysis.py`) carries the actual per-offer tailoring
advice on top of whichever CV file the priority points to.
