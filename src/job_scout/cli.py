import argparse
from pathlib import Path

from job_scout.analysis import analyze_offer
from job_scout.db import get_connection, init_db
from job_scout.enrichment import enrich_offer
from job_scout.export import DEFAULT_EXPORT_PATH, export_to_csv
from job_scout.ingestion import find_offer_files, move_to_errors, move_to_processed, read_offer_file
from job_scout.parser import parse_offer
from job_scout.storage import VALID_STATUSES, save_offer, update_status


def process_offer(conn, path: Path) -> None:
    content = read_offer_file(path)
    offer = parse_offer(content)
    enrichment = enrich_offer(offer.description)
    analysis = analyze_offer(offer, enrichment)
    save_offer(conn, offer, enrichment, analysis, path.name)
    print(f"[{analysis.score}/10, priority {analysis.priority}] {offer.title} - {offer.company}")


def cmd_process() -> None:
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


def cmd_status(offer_id: int, status: str) -> None:
    conn = get_connection()
    try:
        update_status(conn, offer_id, status)
    except ValueError as exc:
        raise SystemExit(f"Error: {exc}") from exc
    finally:
        conn.close()
    print(f"Offer {offer_id} -> {status}")


def cmd_export(output: Path) -> None:
    conn = get_connection()
    path = export_to_csv(conn, output)
    conn.close()
    print(f"Exported to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="job-scout")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "process", help="Process new offer files from the source folder (default)"
    )

    status_parser = subparsers.add_parser("status", help="Update an offer's status")
    status_parser.add_argument("offer_id", type=int)
    status_parser.add_argument("status", choices=sorted(VALID_STATUSES))

    export_parser = subparsers.add_parser("export", help="Export offers to a CSV file")
    export_parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_EXPORT_PATH)

    args = parser.parse_args()

    if args.command in (None, "process"):
        cmd_process()
    elif args.command == "status":
        cmd_status(args.offer_id, args.status)
    elif args.command == "export":
        cmd_export(args.output)


if __name__ == "__main__":
    main()
