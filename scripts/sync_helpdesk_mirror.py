#!/usr/bin/env python3
"""Sync Wrangle ticket status into the Notion Helpdesk Mirror.

Run periodically (cron / launchd / CI):

  source .venv/bin/activate
  python scripts/sync_helpdesk_mirror.py --dry-run
  python scripts/sync_helpdesk_mirror.py

Requires WRANGLE_* inbox IDs, WRANGLE_API_TOKEN, and NOTION_HELPDESK_MIRROR_DB_ID.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import helpdesk_mirror, wrangle_client  # noqa: E402


async def _sync(*, dry_run: bool) -> int:
    if not wrangle_client.configured():
        print("Wrangle is not configured; set WRANGLE_API_TOKEN and related env.")
        return 1
    if not helpdesk_mirror.configured():
        print("Notion mirror is not configured; set NOTION_HELPDESK_MIRROR_DB_ID.")
        return 1

    inboxes = wrangle_client.configured_inbox_ids()
    if not inboxes:
        print("No WRANGLE_INBOX_* ids configured.")
        return 1

    updated = 0
    missing = 0
    for team, inbox_id in inboxes:
        tickets = await wrangle_client.list_inbox_tickets(inbox_id)
        print(f"[{team}] {len(tickets)} ticket(s) from Wrangle")
        for ticket in tickets:
            ticket_id = str(ticket.get("id") or "")
            status = str(ticket.get("status") or "")
            if not ticket_id or not status:
                continue
            if dry_run:
                print(f"  would sync {ticket_id} -> {status}")
                continue
            result = await helpdesk_mirror.update_mirror_status(
                ticket_id,
                status=status,
                resolved=status in {"RESOLVED", "CLOSED"},
            )
            if result is None:
                missing += 1
            else:
                updated += 1
                print(f"  synced {ticket_id} -> {status}")

    print(f"done. updated={updated} missing_mirror_row={missing} dry_run={dry_run}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List status changes without writing to Notion.",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_sync(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
