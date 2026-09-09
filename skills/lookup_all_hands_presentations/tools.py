"""Look up All Hands / townhall / offsite decks from January 2025 onward."""

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
_ARCHIVE_LINK = f"<{_ARCHIVE}|All Hands Slides & Recordings>"

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


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat((value or "").strip()[:10])
    except ValueError:
        return None


def _wanted_type(query: str) -> str | None:
    lowered = query.lower()
    if "offsite" in lowered:
        return "offsite"
    if "townhall" in lowered or "town hall" in lowered:
        return "townhall"
    if "all hands" in lowered or "all-hands" in lowered:
        return "all hands"
    return None


def _year_in_query(query: str) -> int | None:
    match = re.search(r"\b(20\d{2})\b", query)
    return int(match.group(1)) if match else None


def _month_in_query(query: str) -> int | None:
    lowered = query.lower()
    for name, number in _MONTHS.items():
        if name in lowered:
            return number
    return None


def _row_type(row: dict) -> str:
    return str((row.get("fields") or {}).get("Type") or "").strip().lower()


def _row_date(row: dict) -> date:
    return _parse_date((row.get("fields") or {}).get("Date", "") or "") or date.min


_OLDER_WORDS = ("before", "previous", "earlier", "older", "prior", "one back")
_NEWER_WORDS = ("after that", "next one", "newer", "more recent than", "later")


def _direction(query: str) -> str | None:
    """Relative step for follow-ups like 'the one before that'."""
    lowered = query.lower()
    if any(word in lowered for word in _OLDER_WORDS):
        return "older"
    if any(word in lowered for word in _NEWER_WORDS):
        return "newer"
    return None


def _pick_row(
    rows: list[dict],
    query: str,
    *,
    last_date: str = "",
    last_type: str = "",
) -> dict | None:
    wanted = _wanted_type(query)
    year = _year_in_query(query)
    month = _month_in_query(query)
    direction = _direction(query)
    cursor = _parse_date(last_date)

    # "the one before that" carries no type of its own — stay on the type
    # Sara just showed so a follow-up does not jump between All hands and
    # Townhall rows.
    if direction and cursor and not wanted and last_type:
        wanted = last_type.strip().lower()

    candidates = rows
    if wanted:
        candidates = [row for row in candidates if wanted in _row_type(row)]

    if direction and cursor:
        if direction == "older":
            older = [row for row in candidates if _row_date(row) < cursor]
            return older[0] if older else None
        newer = [row for row in candidates if _row_date(row) > cursor]
        return newer[-1] if newer else None

    if year:
        candidates = [row for row in candidates if _row_date(row).year == year]
    if month:
        candidates = [row for row in candidates if _row_date(row).month == month]
    return candidates[0] if candidates else None


def _slack_event(row: dict) -> str:
    fields = row.get("fields") or {}
    title = row.get("title") or fields.get("Title") or "All Hands"
    event_date = fields.get("Date") or ""
    slides = (fields.get("Slides") or "").strip()
    recording = (fields.get("Recording") or "").strip()
    passcode = (fields.get("Passcode") or "").strip()
    lines = [f"The {fields.get('Type') or 'event'} on {event_date} ({title}):"]
    if slides.startswith("http"):
        lines.append(f"- Slides: <{slides}|Slides>")
    else:
        lines.append("- Slides: not listed for this event")
    if recording.startswith("http"):
        rec = f"- Recording: <{recording}|Recording>"
        if passcode:
            rec += f" (passcode `{passcode}`)"
        lines.append(rec)
    else:
        lines.append("- Recording: not listed for this event")
    lines.extend(["", _ARCHIVE_LINK])
    return "\n".join(lines)


@tool(
    description=(
        "Look up All Hands, townhall, or offsite slides and recordings from "
        "January 2025 onward. Pass the user's wording in query."
    )
)
async def get_all_hands_event(
    query: str = "latest all hands",
    context: ToolContext = None,
) -> ToolResult:
    """Return one 2025+ All Hands archive row.

    Args:
        query: The user's request, including type, month, or 'latest'.
    """
    year = _year_in_query(query)
    if year is not None and year < 2025:
        text = (
            "Sara only looks up All Hands, townhall, and offsite slides from "
            f"January 2025 onward. For {year}, open the archive:\n"
            f"{_ARCHIVE_LINK}"
        )
        if context is not None:
            await context.send(text)
        return ToolResult(
            llm_response={
                "ok": True,
                "posted": True,
                "instruction": "The answer was already posted. Do not send another message.",
            }
        )

    source = notion_sources.SOURCES["all_hands"]
    rows = await query_database(
        source.notion_id,
        max_rows=source.max_rows,
        filter=source.database_filter,
        sorts=list(source.database_sorts) or None,
    )

    last_date = ""
    last_type = ""
    if context is not None:
        last_date = str(context.memory.get("last_event_date") or "")
        last_type = str(context.memory.get("last_event_type") or "")

    picked = _pick_row(
        rows,
        query or "latest all hands",
        last_date=last_date,
        last_type=last_type,
    )
    if picked is None:
        stepped_back = bool(_direction(query) and last_date)
        text = (
            (
                "That is as far back as Sara can go — January 2025 is the "
                f"earliest event she looks up. The full archive is {_ARCHIVE_LINK}"
            )
            if stepped_back
            else (
                "Sara only looks up All Hands, townhall, and offsite slides from "
                "January 2025 onward, and there is no matching event in that range. "
                f"The full archive is {_ARCHIVE_LINK}"
            )
        )
        if context is not None:
            await context.send(text)
        return ToolResult(
            llm_response={
                "ok": True,
                "posted": True,
                "instruction": "The answer was already posted. Do not send another message.",
            }
        )

    if context is not None:
        fields = picked.get("fields") or {}
        context.memory.set("last_event_date", str(fields.get("Date") or ""))
        context.memory.set("last_event_type", str(fields.get("Type") or ""))
        await context.send(_slack_event(picked))
    return ToolResult(
        llm_response={
            "ok": True,
            "posted": True,
            "instruction": (
                "The answer was already posted. Do not send another message "
                "or invent URLs."
            ),
        }
    )
