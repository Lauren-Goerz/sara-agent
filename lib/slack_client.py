"""Live Slack Web API helpers for channel list + posting.

Env:
  SLACK_BOT_TOKEN            — Bot User OAuth token xoxb-... (required)
  SLACK_ALLOWED_CHANNELS     — optional comma-separated channel names (without #)
                               If set, list/post are restricted to this allowlist.
"""

from __future__ import annotations

import asyncio
import calendar
import os
from datetime import date, datetime, timezone
from typing import Any

import httpx

_START_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%d %B %Y",
    "%d %b %Y",
)


def parse_start_date(raw: str | None) -> date | None:
    """Parse Slack Start date values (unix seconds or common date strings)."""
    text = (raw or "").strip()
    if not text:
        return None
    if text.isdigit():
        try:
            return datetime.fromtimestamp(int(text), tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in _START_DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def add_calendar_months(start: date, months: int) -> date:
    """Advance ``start`` by whole calendar months, clamping the day if needed."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def within_first_n_months(
    start: date,
    months: int = 6,
    *,
    today: date | None = None,
) -> bool:
    """True when ``today`` is strictly before ``start`` + ``months``."""
    as_of = today or date.today()
    return as_of < add_calendar_months(start, months)

SLACK_BASE = "https://slack.com/api"


class SlackConfigError(RuntimeError):
    """Missing or invalid Slack configuration."""


def _token() -> str:
    token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
    if not token:
        raise SlackConfigError(
            "SLACK_BOT_TOKEN is not set. Add your Slack bot token (xoxb-...) to .env."
        )
    return token


def configured() -> bool:
    return bool(os.environ.get("SLACK_BOT_TOKEN", "").strip())


def _allowed_names() -> set[str] | None:
    raw = os.environ.get("SLACK_ALLOWED_CHANNELS", "").strip()
    if not raw:
        return None
    return {name.strip().lstrip("#").lower() for name in raw.split(",") if name.strip()}


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json; charset=utf-8",
    }


async def _api(method: str, *, params: dict | None = None, json: dict | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        if json is not None:
            resp = await client.post(
                f"{SLACK_BASE}/{method}",
                headers=_headers(),
                json=json,
            )
        else:
            resp = await client.get(
                f"{SLACK_BASE}/{method}",
                headers={"Authorization": f"Bearer {_token()}"},
                params=params or {},
            )
        resp.raise_for_status()
        data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API {method} failed: {data.get('error', data)}")
    return data


async def list_channels(*, limit: int = 200) -> list[dict[str, Any]]:
    """List public channels the bot can see (conversations.list)."""
    data = await _api(
        "conversations.list",
        params={
            "types": "public_channel",
            "exclude_archived": "true",
            "limit": str(limit),
        },
    )
    allowed = _allowed_names()
    channels: list[dict[str, Any]] = []
    for ch in data.get("channels", []):
        name = ch.get("name") or ""
        if allowed is not None and name.lower() not in allowed:
            continue
        channels.append(
            {
                "id": ch.get("id"),
                "name": name,
                "is_private": bool(ch.get("is_private")),
            }
        )
    return channels


async def resolve_channel(name_or_id: str) -> dict[str, Any] | None:
    key = name_or_id.strip().lstrip("#")
    channels = await list_channels()
    for ch in channels:
        if ch["id"] == key or ch["name"].lower() == key.lower():
            return ch
    # If allowlist filtered it out, still try id match via info when it looks like an id.
    if key.startswith("C") and len(key) > 8:
        try:
            data = await _api("conversations.info", params={"channel": key})
            ch = data.get("channel") or {}
            name = ch.get("name") or ""
            allowed = _allowed_names()
            if allowed is not None and name.lower() not in allowed:
                return None
            return {
                "id": ch.get("id"),
                "name": name,
                "is_private": bool(ch.get("is_private")),
            }
        except RuntimeError:
            return None
    return None


async def post_message(
    channel_id: str,
    text: str,
    *,
    enforce_allowlist: bool = True,
) -> dict[str, Any]:
    """Post a message via chat.postMessage and return permalink when available."""
    if enforce_allowlist:
        allowed = _allowed_names()
        if allowed is not None:
            channel = await resolve_channel(channel_id)
            if channel is None:
                raise RuntimeError(
                    f"Channel {channel_id} is not in SLACK_ALLOWED_CHANNELS={sorted(allowed)}"
                )
            channel_id = channel["id"]

    data = await _api(
        "chat.postMessage",
        json={"channel": channel_id, "text": text},
    )
    ts = data.get("ts")
    permalink = None
    if ts:
        try:
            link_data = await _api(
                "chat.getPermalink",
                params={"channel": data.get("channel", channel_id), "message_ts": ts},
            )
            permalink = link_data.get("permalink")
        except RuntimeError:
            permalink = None

    return {
        "ok": True,
        "channel": data.get("channel", channel_id),
        "ts": ts,
        "message": {"text": text},
        "permalink": permalink,
    }


async def get_user_location(slack_user_id: str) -> dict[str, Any]:
    """Read Slack timezone (always) and Location custom field when permitted.

    Timezone comes from ``users.info`` (``users:read``). Custom Location needs
    ``users.profile:read``; if that scope is missing, timezone is still returned.
    """
    user_id = (slack_user_id or "").strip()
    if not user_id.startswith("U"):
        return {"ok": False, "error": "invalid_slack_user_id"}

    result: dict[str, Any] = {
        "ok": True,
        "slack_user_id": user_id,
        "location": None,
        "location_source": None,
        "timezone": None,
        "display_name": None,
        "missing_scope": None,
    }

    try:
        info = await _api("users.info", params={"user": user_id})
        user = info.get("user") or {}
        profile = user.get("profile") or {}
        result["timezone"] = user.get("tz")
        result["display_name"] = (
            profile.get("real_name")
            or profile.get("display_name")
            or user.get("name")
        )
    except RuntimeError as error:
        message = str(error)
        if "missing_scope" in message:
            result["missing_scope"] = "users:read"
        result["ok"] = False
        result["error"] = message
        return result

    try:
        profile_data = await _api(
            "users.profile.get",
            params={"user": user_id, "include_labels": "true"},
        )
    except RuntimeError as error:
        message = str(error)
        if "missing_scope" in message or "users.profile:read" in message:
            # Timezone is already available; Location field just isn't.
            result["missing_scope"] = "users.profile:read"
            return result
        result["ok"] = False
        result["error"] = message
        return result

    profile = profile_data.get("profile") or {}
    fields = profile.get("fields") or {}
    preferred_labels = (
        "location",
        "office",
        "office location",
        "work location",
        "country",
        "based in",
        "city",
    )
    labeled: list[tuple[str, str]] = []
    for field in fields.values():
        if not isinstance(field, dict):
            continue
        label = str(field.get("label") or "").strip()
        value = str(field.get("value") or field.get("alt") or "").strip()
        if label and value:
            labeled.append((label, value))

    for label, value in labeled:
        if label.lower() in preferred_labels:
            result["location"] = value
            result["location_source"] = f"slack_profile:{label}"
            return result

    for label, value in labeled:
        if any(token in label.lower() for token in ("location", "office", "country", "city")):
            result["location"] = value
            result["location_source"] = f"slack_profile:{label}"
            return result

    return result


async def list_workspace_members(*, limit: int = 200) -> list[dict[str, Any]]:
    """List non-bot, active workspace members (paginated users.list)."""
    members: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        params: dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        data = await _api("users.list", params=params)
        for user in data.get("members") or []:
            if not isinstance(user, dict):
                continue
            if user.get("deleted") or user.get("is_bot") or user.get("id") == "USLACKBOT":
                continue
            profile = user.get("profile") or {}
            members.append(
                {
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "real_name": profile.get("real_name") or user.get("real_name"),
                    "display_name": profile.get("display_name") or profile.get("real_name"),
                    "tz": user.get("tz"),
                }
            )
        cursor = (data.get("response_metadata") or {}).get("next_cursor") or ""
        if not cursor:
            break
    return members


def _profile_custom_fields(profile: dict[str, Any]) -> list[tuple[str, str]]:
    fields = profile.get("fields") or {}
    labeled: list[tuple[str, str]] = []
    for field in fields.values():
        if not isinstance(field, dict):
            continue
        label = str(field.get("label") or "").strip()
        value = str(field.get("value") or field.get("alt") or "").strip()
        if label and value:
            labeled.append((label, value))
    return labeled


async def get_user_start_date(slack_user_id: str) -> dict[str, Any]:
    """Read the Slack custom profile field labeled Start date (or close variants).

    Returns keys: ok, slack_user_id, start_date_raw, start_date_label, error,
    missing_scope.
    """
    user_id = (slack_user_id or "").strip()
    result: dict[str, Any] = {
        "ok": True,
        "slack_user_id": user_id,
        "start_date_raw": None,
        "start_date_label": None,
        "error": None,
        "missing_scope": None,
    }
    if not user_id.startswith("U"):
        result["ok"] = False
        result["error"] = "invalid_slack_user_id"
        return result

    last_error = ""
    for attempt in range(4):
        try:
            profile_data = await _api(
                "users.profile.get",
                params={"user": user_id, "include_labels": "true"},
            )
            break
        except RuntimeError as error:
            last_error = str(error)
            if "ratelimited" in last_error.lower() and attempt < 3:
                await asyncio.sleep(1.5 * (attempt + 1))
                continue
            result["ok"] = False
            result["error"] = last_error
            if "missing_scope" in last_error or "users.profile:read" in last_error:
                result["missing_scope"] = "users.profile:read"
            return result
    else:
        result["ok"] = False
        result["error"] = last_error or "profile_fetch_failed"
        return result

    preferred = ("start date", "startdate", "hire date", "hiredate", "start day")
    labeled = _profile_custom_fields(profile_data.get("profile") or {})
    for label, value in labeled:
        if label.lower().strip() in preferred:
            result["start_date_raw"] = value
            result["start_date_label"] = label
            return result
    for label, value in labeled:
        lowered = label.lower()
        if "start" in lowered and "date" in lowered:
            result["start_date_raw"] = value
            result["start_date_label"] = label
            return result
        if "hire" in lowered and "date" in lowered:
            result["start_date_raw"] = value
            result["start_date_label"] = label
            return result
    return result


async def open_dm(slack_user_id: str) -> str:
    """Open (or reuse) a DM channel with a user; return channel id."""
    data = await _api(
        "conversations.open",
        json={"users": slack_user_id},
    )
    channel = data.get("channel") or {}
    channel_id = channel.get("id")
    if not channel_id:
        raise RuntimeError(f"conversations.open returned no channel for {slack_user_id}")
    return str(channel_id)


async def post_dm(slack_user_id: str, text: str) -> dict[str, Any]:
    """DM a user (bypasses SLACK_ALLOWED_CHANNELS). Needs im:write + chat:write."""
    channel_id = await open_dm(slack_user_id)
    return await post_message(channel_id, text, enforce_allowlist=False)
