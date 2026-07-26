# Improvements

Non-priority points noticed during development, not acted on yet.

- **Dedup similarity threshold (0.85) needs real-world tuning.** Validated
  once against a representative synthetic pair (0.97 similarity for a
  genuinely reworded same-job posting vs 0.45 for an unrelated job), but
  true calibration needs observed false positives/negatives on real
  reposts over actual usage - can't be front-loaded into a single dev
  session. Revisit if the tool starts missing obvious reposts or flagging
  unrelated offers as similar.
- **`find_hash_duplicates()` has no `exclude_id` parameter**, unlike
  `find_similar_by_embedding()`. Harmless in the current flow (dedup
  check always runs before the offer is inserted), but would self-match
  if a future feature re-checks an already-stored offer's dedup status.
- **`agency` column stays NULL.** The schema anticipated distinguishing
  "who posted this listing" from "the real end employer", but nothing
  produces a value distinct from `company` today - every offer we can
  parse only has one company/poster name. Could be revisited if a future
  offer format exposes both, or the dedup epic starts inferring it from
  clustering same-job/different-poster pairs.
- **No regression tests for the Claude/VoyageAI-calling modules**
  (`enrichment.py`, `analysis.py`, `profile.py`, `letter.py`, `cli.py`).
  Verified via live runs at each ticket instead, consistent with not
  writing tests unless asked - but if this project grows past
  occasional-use tooling, mocking the Anthropic/Voyage clients would let
  these get real regression coverage.
