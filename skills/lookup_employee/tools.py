"""Employee lookup backed by the Notion "Who's Who" database.

Env:
  NOTION_WHOS_WHO_DB_ID  - database id of the Who's Who page (share it with
                           the Sara-Agent Notion integration).
"""

from __future__ import annotations

import os
import re
import time
from typing import Any

from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import notion_client

_CACHE: dict[str, Any] = {"rows": None, "fetched_at": 0.0}
_CACHE_TTL_SECONDS = 600

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "at",
        "for",
        "from",
        "in",
        "is",
        "of",
        "on",
        "or",
        "our",
        "rasa",
        "the",
        "to",
        "who",
        "whom",
        "whose",
        "with",
    }
)

# Common role acronyms → phrases also present in the Title field.
_ROLE_EXPAND: dict[str, tuple[str, ...]] = {
    "cto": ("chief technology officer", "co-founder & cto", "cofounder & cto"),
    "ceo": ("chief executive officer",),
    "cpo": ("chief product officer",),
    "cro": ("chief revenue officer",),
    "cfo": ("chief financial officer",),
    "coo": ("chief operating officer",),
}


def _db_id() -> str:
    return os.environ.get("NOTION_WHOS_WHO_DB_ID", "").strip()


def _is_person_row(row: dict[str, Any]) -> bool:
    title = str(row.get("title", "")).strip()
    if not title or title == "Untitled" or title.startswith("[Template"):
        return False
    # A real profile has at least one field beyond the name itself.
    return len(row.get("fields") or {}) > 1


async def _roster() -> list[dict[str, Any]]:
    now = time.time()
    if _CACHE["rows"] is not None and now - _CACHE["fetched_at"] < _CACHE_TTL_SECONDS:
        return _CACHE["rows"]
    rows = [r for r in await notion_client.query_database(_db_id()) if _is_person_row(r)]
    _CACHE["rows"] = rows
    _CACHE["fetched_at"] = now
    return rows


def _tokens(query: str) -> list[str]:
    raw = re.findall(r"[a-z0-9&+-]+", query.lower())
    return [t for t in raw if t not in _STOPWORDS and len(t) > 1]


def _word_hit(haystack: str, needle: str) -> bool:
    """True when needle is a whole word/token, not a substring of another word.

    Prevents 'cto' matching inside 'direcTOR'.
    """
    if not needle or not haystack:
        return False
    if " " in needle or "&" in needle:
        return needle in haystack
    return (
        re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack)
        is not None
    )


def _score(row: dict[str, Any], query: str) -> float:
    q = query.lower().strip()
    if not q:
        return 0.0

    name = str(row.get("title", "")).lower()
    fields = {
        str(k).lower(): str(v).lower() for k, v in (row.get("fields") or {}).items()
    }
    role = fields.get("title") or ""
    other = " ".join(v for k, v in fields.items() if k != "title")
    tokens = _tokens(q)
    score = 0.0

    if q == name:
        score += 100
    elif _word_hit(name, q) or q in name:
        score += 50

    for token in tokens:
        if _word_hit(name, token):
            score += 25

    # Job title is what "who is the CTO" should hit — weight it hard.
    for token in tokens:
        if _word_hit(role, token):
            score += 40
        elif _word_hit(other, token):
            score += 5

    for token in tokens:
        for phrase in _ROLE_EXPAND.get(token, ()):
            if phrase in role:
                score += 50

    if len(q) >= 3 and (q == role or _word_hit(role, q)):
        score += 60

    return score


@tool(
    description=(
        "Search Rasa's Who's Who directory (Notion) by name, job title/role, "
        "team, or location. Use for questions like 'who is the CTO' as well as "
        "name lookups."
    )
)
async def search_directory(query: str, context: ToolContext = None) -> ToolResult:
    """Search the Who's Who Notion database.

    Args:
        query: Name, job title/role (e.g. CTO), team, location, or fragment.
    """
    if not notion_client.configured():
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "notion_not_configured",
                "hint": "NOTION_API_KEY is missing; ask IT to configure it.",
            }
        )
    if not _db_id():
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "whos_who_not_configured",
                "hint": (
                    "NOTION_WHOS_WHO_DB_ID is not set. Add the Who's Who "
                    "database id to .env and share the page with the "
                    "Sara-Agent integration."
                ),
            }
        )

    try:
        rows = await _roster()
    except Exception as error:  # noqa: BLE001 - surface API errors to the LLM
        return ToolResult(
            llm_response={
                "ok": False,
                "error": f"notion_error: {error}",
                "hint": (
                    "If this is a 404, the Who's Who page is not shared with "
                    "the Sara-Agent Notion integration yet."
                ),
            }
        )

    scored = sorted(
        ((row, _score(row, query)) for row in rows),
        key=lambda pair: pair[1],
        reverse=True,
    )
    matches = [row for row, score in scored if score > 0][:5]

    return ToolResult(
        llm_response={
            "ok": True,
            "query": query,
            "match_count": len(matches),
            "employees": [
                {
                    "id": row["id"],
                    "name": row["title"],
                    "fields": row["fields"],
                    "notion_url": row["url"],
                }
                for row in matches
            ],
            "hint": (
                None
                if matches
                else "No Who's Who matches. Ask for a different spelling or team."
            ),
        }
    )


@tool(
    description=(
        "Return full Who's Who details (all fields + profile page text) for "
        "the selected employee. Call only after selected_employee_id is set."
    )
)
async def get_employee_details(context: ToolContext = None) -> ToolResult:
    """Return Who's Who row fields and profile page body for the selection."""
    if context is None:
        return ToolResult(llm_response={"ok": False, "error": "no_context"})

    employee_id = context.memory.get("selected_employee_id")
    if not employee_id:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_employee_selected",
                "hint": "Search the directory and select someone first.",
            }
        )

    rows = await _roster()
    row = next((r for r in rows if r["id"] == str(employee_id)), None)
    if row is None:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "unknown_employee",
                "employee_id": employee_id,
            }
        )

    context.memory.set("selected_employee_name", row["title"])

    profile_body = ""
    try:
        page = await notion_client.get_page_with_body(str(employee_id), max_blocks=100)
        body = page.get("body") or ""
        if body and "No readable text blocks" not in body:
            # Drop file/link lines: their signed S3 URLs are huge and useless
            # here, and would otherwise crowd out the actual profile text.
            text_lines = [
                line
                for line in body.splitlines()
                if not line.startswith("[file]") and not line.startswith("[link]")
            ]
            profile_body = "\n".join(text_lines).strip()[:4000]
    except Exception:  # noqa: BLE001 - row fields alone are still useful
        profile_body = ""

    return ToolResult(
        llm_response={
            "ok": True,
            "employee": {
                "name": row["title"],
                "fields": row["fields"],
                "notion_url": row["url"],
                "profile_notes": profile_body or None,
            },
        }
    )
