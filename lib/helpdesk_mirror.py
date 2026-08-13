"""Notion Helpdesk Mirror — reporting rows only (not agent work UI).

Creates/updates pages in the database identified by
``NOTION_HELPDESK_MIRROR_DB_ID``. Expected properties (create these in Notion
and share the DB with Sara's integration):

  Name (title)
  Ticket ID (rich_text)
  Team (select: IT, Ops, HR, Other)
  Status (select: Open, NEW, IN_PROGRESS, ON_HOLD, RESOLVED, CLOSED)
  Wrangle URL (url)
  Requester (rich_text)
  Channel (rich_text)
  Slack ts (rich_text)
  Created (date)
  Resolved (date, optional)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import httpx

from lib import notion_client

# Registered for documentation / allowlist consistency (writes go through
# create_mirror_row, not notion_sources.load).
HELPDESK_MIRROR_KEY = "helpdesk_mirror"


class HelpdeskMirrorConfigError(RuntimeError):
    """Missing Helpdesk Mirror database configuration."""


def configured() -> bool:
    return bool(
        notion_client.configured()
        and os.environ.get("NOTION_HELPDESK_MIRROR_DB_ID", "").strip()
    )


def _database_id() -> str:
    db_id = os.environ.get("NOTION_HELPDESK_MIRROR_DB_ID", "").strip()
    if not db_id:
        raise HelpdeskMirrorConfigError(
            "NOTION_HELPDESK_MIRROR_DB_ID is not set. Create a Helpdesk Mirror "
            "Notion database, share it with Sara's integration, and put the "
            "database id in .env."
        )
    return db_id


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _title_prop(text: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": (text or "Untitled")[:2000]}}]}


def _rich_text_prop(text: str) -> dict[str, Any]:
    return {
        "rich_text": [
            {"type": "text", "text": {"content": (text or "")[:2000]}}
        ]
    }


def _select_prop(name: str) -> dict[str, Any]:
    return {"select": {"name": name}}


def _url_prop(url: str | None) -> dict[str, Any]:
    return {"url": url or None}


def _date_prop(iso_date: str | None) -> dict[str, Any]:
    if not iso_date:
        return {"date": None}
    return {"date": {"start": iso_date}}


async def create_mirror_row(
    *,
    title: str,
    ticket_id: str,
    team: str,
    status: str,
    wrangle_url: str | None,
    requester: str,
    channel: str,
    slack_ts: str,
    created: str | None = None,
) -> dict[str, Any]:
    """Insert a reporting row for a newly created Wrangle ticket."""
    headers = notion_client.api_headers()
    team_name = {
        "it": "IT Support",
        "ops": "General / Ops",
        "hr": "People / HR",
        "finance": "Payhawk / Finance",
        "swag": "Rasa Swag",
        "revops": "Rev Ops",
        "security": "Security and Compliance",
        "software": "Software request",
    }.get((team or "ops").lower(), "General / Ops")
    status_name = status or "Open"
    properties = {
        "Name": _title_prop(title),
        "Ticket ID": _rich_text_prop(ticket_id),
        "Team": _select_prop(team_name),
        "Status": _select_prop(status_name),
        "Wrangle URL": _url_prop(wrangle_url),
        "Requester": _rich_text_prop(requester),
        "Channel": _rich_text_prop(channel),
        "Slack ts": _rich_text_prop(slack_ts),
        "Created": _date_prop(created or _today()),
    }
    payload = {
        "parent": {"database_id": _database_id()},
        "properties": properties,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{notion_client.NOTION_BASE}/pages",
            headers=headers,
            json=payload,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Notion mirror create failed ({response.status_code}): "
                f"{response.text}"
            )
        page = response.json()
    return {
        "id": page.get("id"),
        "url": page.get("url"),
        "ticket_id": ticket_id,
    }


async def find_mirror_page_id(ticket_id: str) -> str | None:
    """Look up the Notion page id for a Wrangle ticket id."""
    headers = notion_client.api_headers()
    payload = {
        "filter": {
            "property": "Ticket ID",
            "rich_text": {"equals": ticket_id},
        },
        "page_size": 1,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{notion_client.NOTION_BASE}/databases/{_database_id()}/query",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    results = data.get("results") or []
    if not results:
        return None
    return str(results[0].get("id") or "") or None


async def update_mirror_status(
    ticket_id: str,
    *,
    status: str,
    resolved: bool = False,
) -> dict[str, Any] | None:
    """Update Status (and Resolved date when closed) for a mirror row."""
    page_id = await find_mirror_page_id(ticket_id)
    if not page_id:
        return None
    headers = notion_client.api_headers()
    properties: dict[str, Any] = {"Status": _select_prop(status)}
    if resolved or status in {"RESOLVED", "CLOSED"}:
        properties["Resolved"] = _date_prop(_today())
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(
            f"{notion_client.NOTION_BASE}/pages/{page_id}",
            headers=headers,
            json={"properties": properties},
        )
        response.raise_for_status()
        page = response.json()
    return {"id": page.get("id"), "url": page.get("url"), "status": status}
