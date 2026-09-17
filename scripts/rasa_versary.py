#!/usr/bin/env python3
"""Proactively DM Rasa employees on their Slack "Start date" anniversary.

Reads each member's Slack custom profile field (Start date), and if today is
their rasa-versary, sends a short DM from Sara.

Usage (from repo root, venv activated, .env loaded):

  # Safe preview - prints who would be congratulated, sends nothing
  python scripts/rasa_versary.py --dry-run

  # Actually send DMs
  python scripts/rasa_versary.py

  # Force a calendar day (useful for testing)
  python scripts/rasa_versary.py --dry-run --date 2026-03-15

Schedule daily (example launchd / cron / GitHub Actions):

  0 9 * * * cd /path/to/maestro-agent && .venv/bin/python scripts/rasa_versary.py

Slack scopes needed on the bot:
  users:read, users.profile:read, im:write, chat:write

Idempotency: .data/rasa_versary_sent.json records user+year so restarts
do not double-DM the same anniversary year.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import slack_client  # noqa: E402

SENT_PATH = ROOT / ".data" / "rasa_versary_sent.json"
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d.%m.%Y",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
)


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def parse_start_date(raw: str) -> date | None:
    """Parse Slack Start date values (unix seconds or common date strings)."""
    text = (raw or "").strip()
    if not text:
        return None
    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text), tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    # ISO with optional time
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def years_completed(start: date, today: date) -> int:
    years = today.year - start.year
    if (today.month, today.day) < (start.month, start.day):
        years -= 1
    return max(years, 0)


def is_anniversary(start: date, today: date) -> bool:
    """True when today matches start month/day (Feb 29 -> Feb 28 in non-leap years)."""
    if start.month == 2 and start.day == 29:
        try:
            date(today.year, 2, 29)
            return today.month == 2 and today.day == 29
        except ValueError:
            return today.month == 2 and today.day == 28
    return today.month == start.month and today.day == start.day


def load_sent() -> dict[str, list[int]]:
    if not SENT_PATH.exists():
        return {}
    try:
        data = json.loads(SENT_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    cleaned: dict[str, list[int]] = {}
    for user_id, years in data.items():
        if isinstance(years, list):
            cleaned[str(user_id)] = [int(y) for y in years if str(y).isdigit() or isinstance(y, int)]
    return cleaned


def save_sent(sent: dict[str, list[int]]) -> None:
    SENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SENT_PATH.write_text(json.dumps(sent, indent=2, sort_keys=True) + "\n")


def already_sent(sent: dict[str, list[int]], user_id: str, year: int) -> bool:
    return year in sent.get(user_id, [])


def mark_sent(sent: dict[str, list[int]], user_id: str, year: int) -> None:
    years = sent.setdefault(user_id, [])
    if year not in years:
        years.append(year)
        years.sort()


def message_for(display_name: str, years: int) -> str:
    first = (display_name or "there").strip().split()[0] or "there"
    if years <= 0:
        return (
            f"Happy first day energy, {first}! Welcome to Rasa - "
            "glad you're here."
        )
    unit = "year" if years == 1 else "years"
    return (
        f"Happy rasa-versary, {first}! :tada: "
        f"Today marks *{years} {unit}* at Rasa. "
        "Thanks for everything you bring to the team."
    )


async def run(*, today: date, dry_run: bool, limit: int | None) -> int:
    if not slack_client.configured():
        print("ERROR: SLACK_BOT_TOKEN is not set.", file=sys.stderr)
        return 1

    sent = load_sent()
    members = await slack_client.list_workspace_members()
    if limit is not None:
        members = members[:limit]

    print(f"Checking {len(members)} Slack members for rasa-versaries on {today.isoformat()}")
    if dry_run:
        print("Dry run: no DMs will be sent.\n")

    congratulated = 0
    skipped_no_date = 0
    skipped_parse = 0
    skipped_not_today = 0
    skipped_already = 0
    errors = 0

    for member in members:
        user_id = member.get("id") or ""
        name = member.get("display_name") or member.get("real_name") or member.get("name") or user_id
        try:
            profile = await slack_client.get_user_start_date(user_id)
        except Exception as exc:  # noqa: BLE001 - keep scanning other users
            print(f"  ! {name}: profile error: {exc}")
            errors += 1
            await asyncio.sleep(0.8)
            continue

        # Stay under Slack users.profile.get rate limits on large workspaces.
        await asyncio.sleep(0.8)

        if not profile.get("ok"):
            err = profile.get("missing_scope") or profile.get("error") or "unknown"
            print(f"  ! {name}: {err}")
            errors += 1
            continue

        raw = profile.get("start_date_raw")
        if not raw:
            skipped_no_date += 1
            continue

        start = parse_start_date(str(raw))
        if start is None:
            print(f"  ? {name}: could not parse Start date {raw!r}")
            skipped_parse += 1
            continue

        if start > today:
            skipped_not_today += 1
            continue

        if not is_anniversary(start, today):
            skipped_not_today += 1
            continue

        years = years_completed(start, today)
        # Day-0 "anniversary" of hire: only congratulate from year 1 onward.
        if years < 1:
            skipped_not_today += 1
            continue

        if already_sent(sent, user_id, today.year):
            print(f"  = {name}: already congratulated for {today.year} ({years}y)")
            skipped_already += 1
            continue

        text = message_for(str(name), years)
        print(f"  * {name}: {years}y since {start.isoformat()} -> DM")
        if dry_run:
            print(f"      {text}")
            congratulated += 1
            continue

        try:
            await slack_client.post_dm(user_id, text)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {name}: DM failed: {exc}")
            errors += 1
            continue

        mark_sent(sent, user_id, today.year)
        save_sent(sent)
        congratulated += 1

    print(
        "\nDone."
        f" congratulated={congratulated}"
        f" no_date={skipped_no_date}"
        f" unparsed={skipped_parse}"
        f" not_today={skipped_not_today}"
        f" already={skipped_already}"
        f" errors={errors}"
    )
    return 1 if errors and congratulated == 0 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="DM Slack users on their rasa-versary")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List matches without sending DMs",
    )
    parser.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Override 'today' for testing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only scan the first N workspace members (debug)",
    )
    args = parser.parse_args()

    _load_dotenv()
    today = date.today()
    if args.date:
        today = date.fromisoformat(args.date)

    return asyncio.run(run(today=today, dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
