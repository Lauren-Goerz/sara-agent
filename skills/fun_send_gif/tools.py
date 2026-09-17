"""Search Giphy and post a GIF into the current Slack thread."""

from __future__ import annotations

import os
import random
import re
from typing import Any

import httpx
import structlog
from rasa.mantle.tools.decorator import ToolContext, tool
from rasa.mantle.tools.result import ToolResult
from slack_sdk.web.async_client import AsyncWebClient

structlogger = structlog.get_logger()

_GIPHY_SEARCH = "https://api.giphy.com/v1/gifs/search"
_RATING = "pg-13"
_BLOCKED = re.compile(
    r"\b("
    r"nsfw|porn|sex|nude|naked|xxx|erotic|fetish|"
    r"kill|murder|gore|blood|suicide|terror|"
    r"racist|nazi|hate"
    r")\b",
    re.IGNORECASE,
)


def _giphy_key() -> str:
    return os.environ.get("GIPHY_API_KEY", "").strip()


def _latest_slack_destination(context: ToolContext) -> tuple[str, str | None] | None:
    for event in reversed(context.events):
        if getattr(event, "input_channel", None) != "slack":
            continue
        metadata = getattr(event, "metadata", None) or {}
        channel = metadata.get("out_channel")
        if channel:
            return str(channel), metadata.get("thread_id")
    return None


def _pick_image_url(images: dict[str, Any]) -> str | None:
    for key in ("downsized", "fixed_height", "original"):
        item = images.get(key) or {}
        url = str(item.get("url") or "").strip()
        if url.startswith("https://"):
            return url
    return None


async def _search_giphy(query: str) -> dict[str, Any] | None:
    params = {
        "api_key": _giphy_key(),
        "q": query,
        "limit": 5,
        "rating": _RATING,
        "lang": "en",
    }
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_GIPHY_SEARCH, params=params)
        response.raise_for_status()
        payload = response.json()
    results = payload.get("data") or []
    if not results:
        return None
    # Prefer a pick among the top results for variety.
    chosen = random.choice(results[: min(5, len(results))])
    images = chosen.get("images") or {}
    url = _pick_image_url(images)
    if not url:
        return None
    return {
        "id": str(chosen.get("id") or ""),
        "title": str(chosen.get("title") or query).strip() or query,
        "gif_url": url,
        "giphy_page": str(chosen.get("url") or "").strip() or None,
    }


@tool(
    description=(
        "Search Giphy and post one workplace-safe GIF into the current Slack "
        "thread. Pass a short search query (e.g. 'celebration', 'facepalm')."
    )
)
async def send_slack_gif(
    query: str = "",
    context: ToolContext = None,
) -> ToolResult:
    """Search Giphy and post a GIF to Slack.

    Args:
        query: Short GIF search phrase (e.g. thumbs up, coffee, high five).
    """
    search = str(query or "").strip()
    if not search:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "missing_query",
                "instruction": "Ask what kind of GIF they want, then call again.",
            }
        )

    if _BLOCKED.search(search):
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "blocked_query",
                "instruction": (
                    "Refuse briefly - that search is not workplace-safe. Offer "
                    "a tame alternative."
                ),
            }
        )

    if not _giphy_key():
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "not_configured",
                "missing_giphy_key": True,
                "instruction": (
                    "Say an admin needs to set GIPHY_API_KEY. Do not invent a GIF."
                ),
            }
        )

    try:
        hit = await _search_giphy(search)
    except Exception as error:  # noqa: BLE001
        structlogger.error("fun_send_gif.giphy_failed", error=str(error), query=search)
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "giphy_failed",
                "message": str(error),
                "instruction": "Say Giphy search failed and ask them to try again.",
            }
        )

    if not hit:
        return ToolResult(
            llm_response={
                "ok": False,
                "error": "no_results",
                "query": search,
                "instruction": "Say no GIF matched; ask for a different search.",
            }
        )

    destination = _latest_slack_destination(context) if context else None
    posted = False
    post_error: str | None = None

    if destination and os.environ.get("SLACK_BOT_TOKEN", "").strip():
        channel, thread_ts = destination
        client = AsyncWebClient(token=os.environ["SLACK_BOT_TOKEN"].strip())
        kwargs: dict[str, Any] = {
            "channel": channel,
            "text": f"GIF: {hit['title']}",
            "blocks": [
                {
                    "type": "image",
                    "image_url": hit["gif_url"],
                    "alt_text": hit["title"][:100],
                }
            ],
        }
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        try:
            await client.chat_postMessage(**kwargs)
            posted = True
        except Exception as error:  # noqa: BLE001
            post_error = str(error)
            structlogger.error(
                "fun_send_gif.slack_post_failed",
                channel=channel,
                thread_ts=thread_ts,
                error=post_error,
            )
    else:
        post_error = "No Slack destination for this conversation."

    return ToolResult(
        llm_response={
            "ok": posted,
            "posted_to_slack": posted,
            "query": search,
            "title": hit["title"],
            "gif_url": hit["gif_url"],
            "giphy_page": hit.get("giphy_page"),
            "post_error": post_error,
            "instruction": (
                "The GIF is already in the Slack thread. Confirm in one short "
                "playful line. Do not dump the URL."
                if posted
                else (
                    "Slack posting failed. Share gif_url so they can open it, "
                    "and apologize briefly."
                )
            ),
        }
    )
