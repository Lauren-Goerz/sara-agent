"""All Hands / townhall / offsite slides and recordings (Jan 2025+)."""

from __future__ import annotations

import re
from datetime import date

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import notion_sources
from lib.notion_client import query_database

_ARCHIVE = (
    "https://app.notion.com/p/rasa/"
    "All-Hands-Slides-Recordings-78c804f648094a2389dd0cc494fe6fec"
)
_ARCHIVE_LINK = f"<{_ARCHIVE}|All Hands: Slides & Recordings>"
_THURSDAY_NOTE = (
    "All Hands is always on a Thursday (usually the last Thursday of the "
    "month) — always double-check your Google Calendar for the exact date."
)
_ORGANIZER_HELP = (
    "If an All Hands recording or slides link doesn't work, reach out to the "
    "meeting organizer first."
)

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
_MONTH_NAMES = {number: name.title() for name, number in _MONTHS.items()}


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat((value or "").strip()[:10])
    except ValueError:
        return None


def _row_date(row: dict) -> date:
    return _parse_date((row.get("fields") or {}).get("Date", "") or "") or date.min


def _row_type(row: dict) -> str:
    return str((row.get("fields") or {}).get("Type") or "").strip().lower()


def _wanted_type(query: str) -> str | None:
    lowered = query.lower()
    mentioned = {
        "offsite": "offsite" in lowered,
        "townhall": "townhall" in lowered or "town hall" in lowered,
        "all hands": "all hands" in lowered or "all-hands" in lowered,
    }
    matched = [name for name, present in mentioned.items() if present]
    return matched[0] if len(matched) == 1 else None


def _requested_period(query: str) -> tuple[int | None, int | None]:
    year_match = re.search(r"\b(20\d{2})\b", query)
    year = int(year_match.group(1)) if year_match else None
    month = None
    lowered = query.lower()
    for name, number in _MONTHS.items():
        if name in lowered:
            month = number
            break
    if month is not None and year is None:
        year = date.today().year
    return year, month


def _wants_next(query: str) -> bool:
    lowered = query.lower()
    return bool(re.search(r"\b(next|upcoming)\b", lowered))


def _wants_organizer_help(query: str) -> bool:
    lowered = query.lower()
    return bool(
        re.search(
            r"doesn'?t work|does not work|\bbroken\b|"
            r"can'?t (open|access|play|view)|cannot (open|access|play|view)|"
            r"who (do|should) i (ask|contact|ping)|who (to|can i) ask|"
            r"link (is )?(dead|wrong|broken|invalid)",
            lowered,
        )
    )


def _filter_rows(rows: list[dict], query: str) -> list[dict]:
    wanted = _wanted_type(query)
    year, month = _requested_period(query)
    candidates = rows
    if wanted:
        candidates = [row for row in candidates if wanted in _row_type(row)]
    if year:
        candidates = [row for row in candidates if _row_date(row).year == year]
    if month:
        candidates = [row for row in candidates if _row_date(row).month == month]
    return candidates


def _pick(rows: list[dict], query: str) -> dict | None:
    if _wants_next(query):
        wanted = _wanted_type(query)
        pool = [row for row in rows if not wanted or wanted in _row_type(row)]
        future = [row for row in pool if _row_date(row) >= date.today()]
        return min(future, key=_row_date) if future else None

    candidates = _filter_rows(rows, query)
    return candidates[0] if candidates else None


def _format_event(row: dict, *, include_thursday_note: bool = False) -> str:
    fields = row.get("fields") or {}
    title = row.get("title") or fields.get("Title") or "All Hands"
    event_date = fields.get("Date") or ""
    slides = (fields.get("Slides") or "").strip()
    recording = (fields.get("Recording") or "").strip()
    passcode = (fields.get("Passcode") or "").strip()

    lines = [f"*{fields.get('Type') or 'All Hands'}* — {event_date} ({title})"]
    if slides.startswith("http"):
        lines.append(f"- Slides: <{slides}|Slides>")
    else:
        lines.append("- Slides: not listed")
    if recording.startswith("http"):
        rec = f"- Recording: <{recording}|Recording>"
        if passcode:
            rec += f" (passcode `{passcode}`)"
        lines.append(rec)
    else:
        lines.append("- Recording: not listed")
    if include_thursday_note:
        lines.extend(["", _THURSDAY_NOTE])
    lines.extend(["", _ARCHIVE_LINK])
    return "\n".join(lines)


def _no_match_message(rows: list[dict], query: str) -> str:
    if _wants_next(query):
        lines = [
            "There isn't a future All Hands in the slides archive yet.",
            _THURSDAY_NOTE,
        ]
        if rows:
            latest = rows[0]
            fields = latest.get("fields") or {}
            lines.append(
                f"Most recent in the archive: {fields.get('Date')} "
                f"({latest.get('title') or fields.get('Title') or 'untitled'})."
            )
        lines.extend(["", _ARCHIVE_LINK])
        return "\n".join(lines)

    year, month = _requested_period(query)
    if month is not None and year is not None:
        label = f"{_MONTH_NAMES[month]} {year}"
        return (
            f"No All Hands for {label} is in the archive yet.\n"
            f"{_THURSDAY_NOTE}\n\n{_ARCHIVE_LINK}"
        )

    return (
        "Sara only has All Hands slides and recordings from January 2025 "
        f"onward. Browse the archive: {_ARCHIVE_LINK}"
    )


@tool(
    description=(
        "Fetch All Hands (or townhall/offsite) slides and recording links for "
        "a date, month, latest, or next event. Also handles broken-link help."
    )
)
async def get_all_hands_event(
    query: str = "latest all hands",
    context: ToolContext = None,
) -> ToolResult:
    """Post slides/recording links for the matching All Hands event.

    Args:
        query: User wording — date/month, latest, next, or broken-link help.
    """
    q = (query or "latest all hands").strip()

    if _wants_organizer_help(q):
        if context is not None:
            await context.send(_ORGANIZER_HELP)
        return ToolResult(
            llm_response={
                "ok": True,
                "posted": True,
                "instruction": "Already posted. Do not send another message.",
            }
        )

    year_match = re.search(r"\b(20\d{2})\b", q)
    if year_match and int(year_match.group(1)) < 2025:
        text = (
            "Sara only has All Hands slides and recordings from January 2025 "
            f"onward. Browse the archive: {_ARCHIVE_LINK}"
        )
        if context is not None:
            await context.send(text)
        return ToolResult(
            llm_response={
                "ok": True,
                "posted": True,
                "instruction": "Already posted. Do not send another message.",
            }
        )

    source = notion_sources.SOURCES["all_hands"]
    rows = await query_database(
        source.notion_id,
        max_rows=source.max_rows,
        filter=source.database_filter,
        sorts=list(source.database_sorts) or None,
    )

    picked = _pick(rows, q)
    if picked is None:
        text = _no_match_message(rows, q)
    else:
        text = _format_event(picked, include_thursday_note=_wants_next(q))

    if context is not None:
        await context.send(text)

    return ToolResult(
        llm_response={
            "ok": True,
            "posted": True,
            "instruction": "Already posted. Do not invent URLs or send another message.",
        }
    )
