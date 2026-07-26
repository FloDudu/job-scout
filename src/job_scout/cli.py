from pathlib import Path

from job_scout.analysis import analyze_offer
from job_scout.db import get_connection, init_db
from job_scout.enrichment import enrich_offer
from job_scout.ingestion import find_offer_files, move_to_errors, move_to_processed, read_offer_file
from job_scout.parser import parse_offer
from job_scout.storage import save_offer


def process_offer(conn, path: Path) -> None:
    content = read_offer_file(path)
    offer = parse_offer(content)
    enrichment = enrich_offer(offer.description)
    analysis = analyze_offer(offer, enrichment)
    save_offer(conn, offer, enrichment, analysis, path.name)
    print(f"[{analysis.score}/10, priority {analysis.priority}] {offer.title} - {offer.company}")


def main() -> None:
    init_db()
    conn = get_connection()

    files = find_offer_files()
    if not files:
        print("No new offers to process.")
        return

    processed = 0
    errors = 0
    for path in files:
        try:
            process_offer(conn, path)
            move_to_processed(path)
            processed += 1
        except Exception as exc:
            # Broad catch is intentional here: this is the outermost boundary
            # of the batch loop, so one bad offer (parsing failure, API
            # error, duplicate source_file) must not crash the rest of the
            # batch. The file goes to ODE_errors/ for manual investigation
            # per ticket #6, never silently dropped.
            print(f"ERROR processing {path.name}: {exc}")
            move_to_errors(path)
            errors += 1

    conn.close()
    print(f"\nDone: {processed} processed, {errors} errors.")


if __name__ == "__main__":
    main()
