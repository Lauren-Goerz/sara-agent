"""Wrangle ticketing API client (create / get tickets).

Env (from https://slack.wrangle.io/integrations after API access is enabled):
  WRANGLE_API_TOKEN
  WRANGLE_SLACK_USER_ID
  WRANGLE_SLACK_WORKSPACE_ID
  WRANGLE_INBOX_* for each Rasa inbox (see _TEAM_INBOX_ENV)
"""

from __future__ import annotations

import os
from typing import Any

import httpx

WRANGLE_BASE = "https://slack.wrangle.io/api/v1"

# Keys match helpdesk_intake `team` values. Labels match Wrangle inbox names.
_TEAM_INBOX_ENV = {
    "ops": "WRANGLE_INBOX_OPS",  # General / Ops request
    "it": "WRANGLE_INBOX_IT",  # IT Support
    "finance": "WRANGLE_INBOX_FINANCE",  # Payhawk / Finance
    "hr": "WRANGLE_INBOX_HR",  # People / HR Issues
    "swag": "WRANGLE_INBOX_SWAG",  # Rasa Swag
    "revops": "WRANGLE_INBOX_REVOPS",  # Rev Ops
    "security": "WRANGLE_INBOX_SECURITY",  # Security and Compliance
    "software": "WRANGLE_INBOX_SOFTWARE",  # Software request
}

_TEAM_LABELS = {
    "ops": "General / Ops request",
    "it": "IT Support",
    "finance": "Payhawk / Finance",
    "hr": "People / HR Issues",
    "swag": "Rasa Swag",
    "revops": "Rev Ops",
    "security": "Security and Compliance",
    "software": "Software request",
}

VALID_TEAMS = frozenset(_TEAM_INBOX_ENV)


class WrangleConfigError(RuntimeError):
    """Missing or invalid Wrangle configuration."""


def configured() -> bool:
    return bool(
        os.environ.get("WRANGLE_API_TOKEN", "").strip()
        and os.environ.get("WRANGLE_SLACK_USER_ID", "").strip()
        and os.environ.get("WRANGLE_SLACK_WORKSPACE_ID", "").strip()
    )


def _headers() -> dict[str, str]:
    token = os.environ.get("WRANGLE_API_TOKEN", "").strip()
    if not token:
        raise WrangleConfigError(
            "WRANGLE_API_TOKEN is not set. Enable the Wrangle API and add the "
            "token from https://slack.wrangle.io/integrations to .env."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _auth_query() -> dict[str, str]:
    user_id = os.environ.get("WRANGLE_SLACK_USER_ID", "").strip()
    workspace_id = os.environ.get("WRANGLE_SLACK_WORKSPACE_ID", "").strip()
    if not user_id or not workspace_id:
        raise WrangleConfigError(
            "WRANGLE_SLACK_USER_ID and WRANGLE_SLACK_WORKSPACE_ID are required."
        )
    return {"slackUserId": user_id, "slackWorkspaceId": workspace_id}


def normalize_team(team: str) -> str:
    key = (team or "ops").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "other": "ops",
        "general": "ops",
        "people": "hr",
        "payhawk": "finance",
        "salesforce": "revops",
        "gong": "revops",
        "compliance": "security",
        "tool": "software",
        "license": "software",
    }
    key = aliases.get(key, key)
    return key if key in VALID_TEAMS else "ops"


def inbox_id_for_team(team: str) -> str | None:
    """Return the configured Wrangle inbox UUID for a helpdesk team key."""
    key = normalize_team(team)
    env_name = _TEAM_INBOX_ENV[key]
    value = os.environ.get(env_name, "").strip()
    if value:
        return value
    if key != "ops":
        # Safe fallback only when the specific inbox is unset.
        return os.environ.get("WRANGLE_INBOX_OPS", "").strip() or None
    return None


def team_label(team: str) -> str:
    return _TEAM_LABELS.get(normalize_team(team), _TEAM_LABELS["ops"])


def configured_inbox_ids() -> list[tuple[str, str]]:
    """Return [(team_key, inbox_id), ...] for every configured inbox."""
    pairs: list[tuple[str, str]] = []
    for team, env_name in _TEAM_INBOX_ENV.items():
        value = os.environ.get(env_name, "").strip()
        if value:
            pairs.append((team, value))
    return pairs


def _as_form_fields(raw: Any) -> list[dict[str, Any]]:
    """Normalize inbox formFields to a list of field dicts."""
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        # Some payloads nest fields; accept common shapes.
        for key in ("fields", "items", "formFields"):
            nested = raw.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
        if raw.get("fieldId") or raw.get("fieldLabel"):
            return [raw]
    return []


async def get_inbox(inbox_id: str) -> dict[str, Any]:
    """Fetch one Wrangle inbox (includes form field definitions)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{WRANGLE_BASE}/inboxes/{inbox_id}",
            headers=_headers(),
            params=_auth_query(),
        )
        response.raise_for_status()
        data = response.json()
    inbox = data.get("inbox") if isinstance(data, dict) and "inbox" in data else data
    if not isinstance(inbox, dict) or not inbox.get("id"):
        raise RuntimeError(f"Wrangle get inbox returned unexpected payload: {data!r}")
    return inbox


def find_form_field(
    inbox: dict[str, Any],
    *,
    label_contains: str,
) -> dict[str, Any] | None:
    """Find a form field whose label contains the given text (case-insensitive)."""
    needle = label_contains.strip().lower()
    for field in _as_form_fields(inbox.get("formFields")):
        label = str(field.get("fieldLabel") or "").strip().lower()
        if needle and needle in label:
            return field
    return None


def build_form_field_values(
    inbox: dict[str, Any],
    *,
    label_to_value: dict[str, str],
) -> list[dict[str, Any]]:
    """Map human labels → values into Wrangle formFieldValues entries."""
    values: list[dict[str, Any]] = []
    for label_part, value in label_to_value.items():
        if value is None or str(value).strip() == "":
            continue
        field = find_form_field(inbox, label_contains=label_part)
        if not field or not field.get("fieldId"):
            continue
        values.append({"fieldId": str(field["fieldId"]), "value": str(value)})
    return values


async def create_ticket(
    *,
    inbox_id: str,
    name: str,
    description: str,
    requester_slack_user_id: str,
    priority: str = "NORMAL",
    tags: list[str] | None = None,
    form_field_values: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create a Wrangle ticket. Returns the ticket object from the API."""
    if not inbox_id:
        raise WrangleConfigError("inbox_id is required to create a ticket.")
    if not requester_slack_user_id:
        raise WrangleConfigError("requester_slack_user_id is required.")

    payload: dict[str, Any] = {
        "inboxId": inbox_id,
        "name": name[:200] or "Helpdesk request",
        "requesterId": requester_slack_user_id,
        "description": description or name,
        "priority": priority if priority in {"CRITICAL", "HIGH", "NORMAL", "LOW"} else "NORMAL",
    }
    if tags:
        payload["tags"] = tags
    if form_field_values:
        payload["formFieldValues"] = form_field_values

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{WRANGLE_BASE}/tickets",
            headers=_headers(),
            params=_auth_query(),
            json=payload,
        )
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("error") or detail
            except Exception:  # noqa: BLE001
                pass
            raise RuntimeError(f"Wrangle create ticket failed ({response.status_code}): {detail}")
        data = response.json()

    ticket = data.get("ticket") if isinstance(data, dict) else None
    if not isinstance(ticket, dict) or not ticket.get("id"):
        raise RuntimeError(f"Wrangle create ticket returned unexpected payload: {data!r}")
    return ticket


async def get_ticket(ticket_id: str) -> dict[str, Any]:
    """Fetch a Wrangle ticket by id."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{WRANGLE_BASE}/tickets/{ticket_id}",
            headers=_headers(),
            params=_auth_query(),
        )
        response.raise_for_status()
        data = response.json()

    ticket = data.get("ticket") if isinstance(data, dict) and "ticket" in data else data
    if not isinstance(ticket, dict) or not ticket.get("id"):
        raise RuntimeError(f"Wrangle get ticket returned unexpected payload: {data!r}")
    return ticket


async def list_inbox_tickets(
    inbox_id: str,
    *,
    page: int = 1,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """List tickets for an inbox (for Notion status sync)."""
    params = {
        **_auth_query(),
        "page": str(page),
        "pageSize": str(min(page_size, 200)),
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{WRANGLE_BASE}/inboxes/{inbox_id}/tickets",
            headers=_headers(),
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    tickets = data.get("tickets") if isinstance(data, dict) else None
    return list(tickets or [])
