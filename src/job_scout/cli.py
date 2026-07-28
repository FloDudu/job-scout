import argparse
import sys
from pathlib import Path
from typing import Literal, cast

from job_scout.analysis import analyze_offer, compute_action
from job_scout.db import get_connection, init_db
from job_scout.dedup import embed_text, find_hash_duplicates, find_similar_by_embedding
from job_scout.enrichment import enrich_offer
from job_scout.export import (
    DEFAULT_BRIEF_PATH,
    DEFAULT_EXPORT_PATH,
    export_brief,
    export_to_csv,
    format_offer_report,
)
from job_scout.ingestion import find_offer_files, move_to_errors, move_to_processed, read_offer_file
from job_scout.letter import generate_cover_letter
from job_scout.parser import parse_offer
from job_scout.storage import VALID_STATUSES, get_offer, list_offers, save_offer, update_status

# Windows consoles default to a legacy codepage, not UTF-8 - without this,
# accented company/title names (very common here) print as mojibake instead
# of raising, so it's easy to miss. Guarded: reconfigure() can be unavailable
# on some redirected streams.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass


def process_offer(conn, path: Path) -> None:
    content = read_offer_file(path)
    offer = parse_offer(content)

    print("  enriching...", flush=True)
    enrichment = enrich_offer(offer.description)

    # Two-tier dedup: hash first (free), embedding only if the hash tier
    # found nothing (see #9). A hash-duplicate offer isn't embedded itself -
    # future reworded reposts of the same job still get caught via whichever
    # earlier instance of this text *did* get embedded.
    similar_offers = find_hash_duplicates(conn, offer.description)
    embedding = None
    if not similar_offers:
        print("  checking for duplicates...", flush=True)
        embedding = embed_text(offer.description)
        similar_offers = find_similar_by_embedding(conn, embedding)

    print("  analyzing...", flush=True)
    # Never auto-skip on a match (per #12) - always analyze and let the
    # report flag the duplicate so the user decides.
    analysis = analyze_offer(offer, enrichment, similar_offers=similar_offers)
    save_offer(conn, offer, enrichment, analysis, path.name, embedding=embedding)
    action = compute_action(analysis.score)
    print(
        f"[{analysis.score}/10, priority {analysis.priority}, {action}] "
        f"{offer.title} - {offer.company}",
        flush=True,
    )


def cmd_process() -> None:
    init_db()
    conn = get_connection()

    files = find_offer_files()
    if not files:
        print("No new offers to process.")
        return

    print(f"Found {len(files)} offer(s) to process.", flush=True)

    processed = 0
    errors = 0
    for i, path in enumerate(files, start=1):
        print(f"[{i}/{len(files)}] Processing {path.name}...", flush=True)
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
            print(f"ERROR processing {path.name}: {exc}", flush=True)
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


def cmd_letter(offer_id: int, language: Literal["fr", "en"]) -> None:
    conn = get_connection()
    offer = get_offer(conn, offer_id)
    conn.close()

    if offer is None:
        raise SystemExit(f"Error: No offer with id {offer_id}.")

    letter = generate_cover_letter(
        offer["title"], offer["company"], offer["description"], offer["report"], language
    )
    print(letter)


def cmd_list(date: str | None, actionable: bool) -> None:
    conn = get_connection()
    offers = list_offers(conn, date=date)
    conn.close()

    if actionable:
        offers = [o for o in offers if compute_action(o["score"]) != "Passe"]

    if not offers:
        print("No matching offers.")
        return

    print(f"{'ID':<4} {'SCORE':<6} {'ACTION':<20} {'PRIO':<5} {'STATUS':<12} TITLE - COMPANY")
    for offer in offers:
        score_str = f"{offer['score']}/10"
        action = compute_action(offer["score"])
        print(
            f"{offer['id']:<4} {score_str:<6} {action:<20} "
            f"{offer['priority']:<5} {offer['status']:<12} {offer['title']} - {offer['company']}"
        )


def cmd_show(offer_id: int) -> None:
    conn = get_connection()
    offer = get_offer(conn, offer_id)
    conn.close()

    if offer is None:
        raise SystemExit(f"Error: No offer with id {offer_id}.")

    print(format_offer_report(offer))


def cmd_brief(date: str | None, actionable: bool, output: Path) -> None:
    conn = get_connection()
    offers = list_offers(conn, date=date)
    if actionable:
        offers = [o for o in offers if compute_action(o["score"]) != "Passe"]
    # get_offer() is typed as possibly-None (unknown id), but every id here
    # came from list_offers() on the same table - the walrus filter keeps
    # mypy honest without changing behavior.
    full_offers = [fo for o in offers if (fo := get_offer(conn, o["id"])) is not None]
    conn.close()

    if not full_offers:
        print("No matching offers.")
        return

    path = export_brief(full_offers, output)
    print(f"Wrote {len(full_offers)} offer(s) to {path}")


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

    letter_parser = subparsers.add_parser("letter", help="Generate a cover letter for an offer")
    letter_parser.add_argument("offer_id", type=int)
    letter_parser.add_argument("language", choices=["fr", "en"])

    show_parser = subparsers.add_parser("show", help="Show an offer's full report")
    show_parser.add_argument("offer_id", type=int)

    list_parser = subparsers.add_parser(
        "list", help="List all offers sorted by score, with derived action"
    )
    list_parser.add_argument("--date", help="Only offers captured on this date (YYYY-MM-DD)")
    list_parser.add_argument(
        "--actionable",
        action="store_true",
        help="Only offers where action is Postule or Candidature légère",
    )

    brief_parser = subparsers.add_parser(
        "brief", help="Export full reports (like show) for matching offers to a text file"
    )
    brief_parser.add_argument("--date", help="Only offers captured on this date (YYYY-MM-DD)")
    brief_parser.add_argument(
        "--actionable",
        action="store_true",
        help="Only offers where action is Postule or Candidature légère",
    )
    brief_parser.add_argument("output", type=Path, nargs="?", default=DEFAULT_BRIEF_PATH)

    args = parser.parse_args()

    if args.command in (None, "process"):
        cmd_process()
    elif args.command == "status":
        cmd_status(args.offer_id, args.status)
    elif args.command == "export":
        cmd_export(args.output)
    elif args.command == "letter":
        # argparse's choices=["fr", "en"] guarantees this at runtime.
        cmd_letter(args.offer_id, cast(Literal["fr", "en"], args.language))
    elif args.command == "show":
        cmd_show(args.offer_id)
    elif args.command == "list":
        cmd_list(args.date, args.actionable)
    elif args.command == "brief":
        cmd_brief(args.date, args.actionable, args.output)


if __name__ == "__main__":
    main()
