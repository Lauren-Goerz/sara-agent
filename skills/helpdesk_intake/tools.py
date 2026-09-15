"""Helpdesk intake: classify, create Wrangle ticket, mirror to Notion."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import httpx
import structlog
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult

from lib import wrangle_client

_ROOT = Path(__file__).resolve().parents[2]
structlogger = structlog.get_logger()

_DEDUP_PATH = _ROOT / ".data" / "helpdesk_tickets.json"
_TITLE_CLEAN = re.compile(r"\s+")
_PRIORITY_MAP = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "normal": "NORMAL",
    "low": "LOW",
}

_IT_CATEGORIES = {
    "account access": "Account Access",
    "account": "Account Access",
    "access": "Account Access",
    "hardware issue": "Hardware Issue",
    "hardware": "Hardware Issue",
    "laptop issue": "Laptop Issue",
    "laptop": "Laptop Issue",
    "macbook": "Laptop Issue",
    "other": "Other",
    "software issue": "Software Issue",
    "software": "Software Issue",
    "technical difficulties": "Technical Difficulties",
    "technical": "Technical Difficulties",
    "vpn": "Technical Difficulties",
    "network": "Technical Difficulties",
}

_SECURITY_CATEGORIES = {
    "customer questionnaire": "Customer Questionnaire",
    "questionnaire": "Customer Questionnaire",
    "rfp": "Customer Questionnaire",
    "rfi": "Customer Questionnaire",
    "general enquiry": "General Enquiry",
    "general inquiry": "General Enquiry",
    "enquiry": "General Enquiry",
    "inquiry": "General Enquiry",
    "security incident": "Security Incident",
    "incident": "Security Incident",
    "breach": "Security Incident",
    "vulnerability": "Security Incident",
}

_IT_URGENCIES = {
    "urgent": "Urgent",
    "not urgent": "Not Urgent",
    "not_urgent": "Not Urgent",
    "timely": "Timely",
}

_URGENCY_TO_PRIORITY = {
    "Urgent": "HIGH",
    "Timely": "NORMAL",
    "Not Urgent": "LOW",
}

_DEADLINE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_COST_RE = re.compile(r"[^\d.]")


def _normalize_priority(raw: str) -> str:
    key = (raw or "normal").strip().lower()
    return _PRIORITY_MAP.get(key, "NORMAL")


def _normalize_it_category(raw: str) -> str:
    key = (raw or "").strip().lower()
    if not key:
        return "Other"
    if key in _IT_CATEGORIES:
        return _IT_CATEGORIES[key]
    for alias, label in _IT_CATEGORIES.items():
        if alias in key or key in alias:
            return label
    return "Other"


def _normalize_security_category(raw: str) -> str:
    key = (raw or "").strip().lower()
    if not key:
        return "General Enquiry"
    if key in _SECURITY_CATEGORIES:
        return _SECURITY_CATEGORIES[key]
    for alias, label in _SECURITY_CATEGORIES.items():
        if alias in key or key in alias:
            return label
    return "General Enquiry"


def _normalize_it_urgency(raw: str) -> str:
    key = (raw or "timely").strip().lower().replace("-", " ")
    return _IT_URGENCIES.get(key, "Timely")


def _normalize_deadline(raw: str) -> str:
    """Return YYYY-MM-DD or empty string if missing/invalid."""
    value = (raw or "").strip()
    if not value:
        return ""
    if _DEADLINE_RE.fullmatch(value):
        return value
    return ""


def _normalize_cost(raw: str) -> str:
    """Return digits-only cost (optional decimal). Strip currency symbols."""
    value = (raw or "").strip()
    if not value:
        return ""
    cleaned = _COST_RE.sub("", value.replace(",", ""))
    if not cleaned or cleaned.count(".") > 1:
        return ""
    if cleaned.startswith("."):
        cleaned = f"0{cleaned}"
    if cleaned.endswith("."):
        cleaned = cleaned[:-1]
    return cleaned


def _priority_label(priority_value: str) -> str:
    return {
        "CRITICAL": "Critical",
        "HIGH": "High",
        "NORMAL": "Normal",
        "LOW": "Low",
    }.get(priority_value, "Normal")


def _load_dedup() -> dict[str, Any]:
    if not _DEDUP_PATH.exists():
        return {}
    try:
        return json.loads(_DEDUP_PATH.read_text())
    except Exception:  # noqa: BLE001
        return {}


def _save_dedup(data: dict[str, Any]) -> None:
    _DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DEDUP_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))


def _dedup_key(channel_id: str, message_ts: str) -> str:
    return f"{channel_id}:{message_ts}"


def _latest_slack_meta(context: ToolContext | None) -> dict[str, Any]:
    if context is None:
        return {}
    for event in reversed(context.events):
        if getattr(event, "input_channel", None) != "slack":
            continue
        metadata = getattr(event, "metadata", None) or {}
        return dict(metadata)
    return {}


def _short_title(text: str) -> str:
    cleaned = _TITLE_CLEAN.sub(" ", (text or "").strip())
    if len(cleaned) <= 80:
        return cleaned or "Helpdesk request"
    return cleaned[:77].rstrip() + "..."


def _draft_reply(*, team: str, request_text: str, sensitive: bool) -> str:
    team_label = wrangle_client.team_label(team)
    if sensitive:
        return (
            f"Thanks for reaching out - I've routed this to the {team_label} "
            "inbox privately. An agent will follow up with you directly."
        )
    snippet = _TITLE_CLEAN.sub(" ", (request_text or "").strip())
    if len(snippet) > 160:
        snippet = snippet[:157].rstrip() + "..."
    return (
        f"Thanks for the note about \"{snippet}\". I've opened a ticket for "
        f"the {team_label} team and someone will pick it up shortly."
    )


@tool(
    description=(
        "Create a Rasa Wrangle ticket for a request that needs a person to "
        "action it, and return an AI draft reply. Wrangle is the only "
        "ticketing system. Pass team as one of: ops, it, finance, hr, swag, revops, "
        "security, software. IT needs request_category + urgency. Security "
        "needs request_category + optional deadline (YYYY-MM-DD). Software "
        "needs reason + optional cost (numbers only). Priority for "
        "ops/finance/security/software is Critical/High/Normal/Low."
    )
)
async def create_helpdesk_ticket(
    request_text: str = "",
    team: str = "ops",
    priority: str = "Normal",
    request_category: str = "",
    urgency: str = "Timely",
    anything_else: str = "",
    deadline: str = "",
    reason: str = "",
    cost: str = "",
    is_sensitive_hr: bool = False,
    context: ToolContext = None,
) -> ToolResult:
    """Create a Wrangle ticket + Notion mirror row for helpdesk intake.

    Args:
        request_text: Full employee request text from the Slack message.
        team: Target Wrangle inbox key - ops, it, finance, hr, swag, revops,
            security, or software.
        priority: Ops/Finance/Security/Software priority - Critical, High,
            Normal, Low.
        request_category: IT: Account Access, Hardware Issue, Laptop Issue,
            Other, Software Issue, or Technical Difficulties. Security:
            Customer Questionnaire, General Enquiry, or Security Incident.
        urgency: IT Urgency - Urgent, Not Urgent, or Timely.
        anything_else: Optional IT "Anything else?" notes.
        deadline: Optional Security deadline as YYYY-MM-DD.
        reason: Software request reason ("The reason please").
        cost: Software monthly or annual cost, numbers only (no currency).
        is_sensitive_hr: True when the request is private HR and should not be
            echoed back into the public channel.
    """
    meta = _latest_slack_meta(context)
    channel_id = str(meta.get("out_channel") or meta.get("channel_id") or "").strip()
    message_ts = str(meta.get("message_ts") or "").strip()
    thread_ts = str(
        meta.get("thread_ts") or meta.get("thread_id") or ""
    ).strip()
    parent_ts = str(
        meta.get("helpdesk_parent_ts") or thread_ts or message_ts
    ).strip()
    requester_id = str(meta.get("slack_user_id") or "").strip()

    dedup = _load_dedup()
    if channel_id and parent_ts:
        existing = dedup.get(_dedup_key(channel_id, parent_ts))
        if existing:
            return ToolResult(
                llm_response={
                    "ok": True,
                    "already_ticketed": True,
                    "ticket_id": existing.get("ticket_id"),
                    "ticket_url": existing.get("ticket_url"),
                    "team": existing.get("team"),
                    "instruction": (
                        "A ticket already exists for this helpdesk thread. "
                        "Do not create another. Share the existing ticket_url "
                        "if helpful, otherwise stay quiet or answer briefly."
                    ),
                }
            )

    team_key = wrangle_client.normalize_team(team)
    if is_sensitive_hr:
        team_key = "hr"

    text = (request_text or "").strip()
    if not text:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "missing_request_text",
                "instruction": "Ask what they need help with, then call again.",
            }
        )

    if context is not None:
        context.memory.set("helpdesk_team", team_key)

    suggested = _draft_reply(team=team_key, request_text=text, sensitive=is_sensitive_hr)
    title = _short_title(text)
    anything_else_value = (anything_else or "").strip()
    deadline_value = _normalize_deadline(deadline)
    reason_value = (reason or "").strip()
    cost_value = _normalize_cost(cost)

    if team_key == "it":
        category_value = _normalize_it_category(request_category)
        urgency_value = _normalize_it_urgency(urgency)
        priority_value = _URGENCY_TO_PRIORITY.get(urgency_value, "NORMAL")
    elif team_key == "security":
        category_value = _normalize_security_category(request_category)
        urgency_value = ""
        priority_value = _normalize_priority(priority)
        if category_value == "Security Incident" and priority_value == "NORMAL":
            priority_value = "HIGH"
    else:
        category_value = ""
        urgency_value = ""
        priority_value = _normalize_priority(priority)

    description = text
    if is_sensitive_hr:
        description = (
            "[Sensitive HR request - details in original Slack message. "
            "Do not discuss in the public channel.]\n\n"
            f"{text}"
        )
    elif team_key == "software":
        extras: list[str] = []
        if reason_value:
            extras.append(f"Reason: {reason_value}")
        if cost_value:
            extras.append(f"Monthly or annual cost: {cost_value}")
        if extras:
            description = f"{text}\n\n" + "\n".join(extras)
    elif anything_else_value:
        description = f"{text}\n\nAnything else: {anything_else_value}"

    inbox_id = wrangle_client.inbox_id_for_team(team_key)
    if not wrangle_client.configured() or not inbox_id or not requester_id:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "needs_manual_wrangle",
                "team": team_key,
                "team_label": wrangle_client.team_label(team_key),
                "priority": priority_value,
                "request_category": category_value or None,
                "urgency": urgency_value or None,
                "deadline": deadline_value or None,
                "reason": reason_value or None,
                "cost": cost_value or None,
                "suggested_reply": suggested,
                "privacy_warning": bool(is_sensitive_hr),
                "instruction": (
                    "Wrangle API is not fully configured (token, workspace, "
                    "inbox ids, or requester id missing). Tell the employee to "
                    f"type /wrangle and open a ticket in the "
                    f"{wrangle_client.team_label(team_key)} inbox. Share "
                    "suggested_reply as optional wording. Do not invent a "
                    "ticket id."
                ),
            }
        )

    form_field_values: list[dict[str, Any]] = []
    if team_key in {"it", "security", "software"}:
        try:
            inbox = await wrangle_client.get_inbox(inbox_id)
            if team_key == "it":
                label_to_value = {
                    "summary": title,
                    "detailed description": text,
                    "request category": category_value,
                    "anything else": anything_else_value,
                    "urgency": urgency_value,
                }
            elif team_key == "security":
                label_to_value = {
                    "summary": title,
                    "detailed description": text,
                    "priority": _priority_label(priority_value),
                    "request category": category_value,
                    "deadline": deadline_value,
                }
            else:
                label_to_value = {
                    "ticket name": title,
                    "describe the issue": text,
                    "priority": _priority_label(priority_value),
                    "reason": reason_value,
                    "cost": cost_value,
                }
            form_field_values = wrangle_client.build_form_field_values(
                inbox,
                label_to_value=label_to_value,
            )
        except Exception as error:  # noqa: BLE001
            structlogger.warning(
                "helpdesk.form_fields_failed",
                error=str(error),
                inbox_id=inbox_id,
                team=team_key,
            )

    try:
        ticket = await wrangle_client.create_ticket(
            inbox_id=inbox_id,
            name=title,
            description=description,
            requester_slack_user_id=requester_id,
            priority=priority_value,
            tags=["sara-helpdesk", team_key]
            + ([category_value] if category_value else []),
            form_field_values=form_field_values or None,
        )
    except (wrangle_client.WrangleConfigError, RuntimeError, httpx.HTTPError) as error:
        structlogger.error("helpdesk.wrangle_create_failed", error=str(error))
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "wrangle_create_failed",
                "message": str(error),
                "team": team_key,
                "team_label": wrangle_client.team_label(team_key),
                "suggested_reply": suggested,
                "instruction": (
                    "Say ticket creation failed briefly and ask them to use "
                    f"/wrangle for the {wrangle_client.team_label(team_key)} "
                    "inbox."
                ),
            }
        )

    ticket_id = str(ticket.get("id") or "")
    ticket_url = (
        str(ticket.get("slackPermalinkUrl") or "").strip()
        or str((ticket.get("slackOriginalMessage") or {}).get("permalinkUrl") or "").strip()
    )
    status = str(ticket.get("status") or "NEW")
    number = ticket.get("workspaceTicketNumber")
    display_id = f"#{number}" if number is not None else ticket_id

    if context is not None:
        context.memory.set("ticket_id", ticket_id)
        if ticket_url:
            context.memory.set("ticket_url", ticket_url)

    if channel_id and parent_ts and ticket_id:
        dedup[_dedup_key(channel_id, parent_ts)] = {
            "ticket_id": ticket_id,
            "ticket_url": ticket_url,
            "team": team_key,
            "created_at": time.time(),
        }
        _save_dedup(dedup)

    return ToolResult(
        llm_response={
            "ok": True,
            "already_ticketed": False,
            "ticket_id": ticket_id,
            "display_id": display_id,
            "ticket_url": ticket_url,
            "status": status,
            "team": team_key,
            "team_label": wrangle_client.team_label(team_key),
            "priority": priority_value,
            "request_category": category_value or None,
            "urgency": urgency_value or None,
            "deadline": deadline_value or None,
            "reason": reason_value or None,
            "cost": cost_value or None,
            "anything_else": anything_else_value or None,
            "form_fields_set": len(form_field_values),
            "ticket_name": title,
            "suggested_reply": suggested,
            "privacy_warning": bool(is_sensitive_hr),
            "instruction": (
                "Confirm the Wrangle ticket in one short Slack message. Share "
                "ticket_url as <url|label> when present. Include suggested_reply "
                "as a clearly labeled draft for agents. Wrangle is the only "
                "place tickets live. "
                "If privacy_warning is true, do not restate private details."
            ),
        }
    )
