"""Live Slack Web API helpers for channel list + posting.

Env:
  SLACK_BOT_TOKEN            — Bot User OAuth token xoxb-... (required)
  SLACK_ALLOWED_CHANNELS     — optional comma-separated channel names (without #)
                               If set, list/post are restricted to this allowlist.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

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


async def post_message(channel_id: str, text: str) -> dict[str, Any]:
    """Post a message via chat.postMessage and return permalink when available."""
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
