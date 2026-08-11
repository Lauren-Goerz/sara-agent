"""Employee lookup backed by the Notion "Who's Who" database.

Env:
  NOTION_WHOS_WHO_DB_ID  - database id of the Who's Who page (share it with
                           the Sara-Agent Notion integration).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

from rasa.calm_v2.tools.decorator import ToolContext, tool
from rasa.calm_v2.tools.result import ToolResult

# Allow importing shared clients from project lib/
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from lib import notion_client  # noqa: E402

_CACHE: dict[str, Any] = {"rows": None, "fetched_at": 0.0}
_CACHE_TTL_SECONDS = 600


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


def _score(row: dict[str, Any], query: str) -> float:
    q = query.lower().strip()
    if not q:
        return 0.0
    title = str(row.get("title", "")).lower()
    score = 0.0
    tokens = [t for t in q.replace(",", " ").split() if t]
    if q == title:
        score += 100
    if q in title:
        score += 50
    for token in tokens:
        if token in title:
            score += 20
    other = " ".join(str(v).lower() for v in (row.get("fields") or {}).values())
    for token in tokens:
        if token in other:
            score += 5
    return score


@tool(
    description=(
        "Search Rasa's Who's Who directory (Notion) by name, team, role, or "
        "location."
    )
)
async def search_directory(query: str, context: ToolContext = None) -> ToolResult:
    """Search the Who's Who Notion database.

    Args:
        query: Name, team, role, location, or other fragment to look for.
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
